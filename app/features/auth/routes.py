"""
Authentication routes - FastAPI route handlers.
"""
import logging
from datetime import timedelta
from typing import Any
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.base_client.errors import OAuthError
from urllib.parse import urlencode
from jose import JWTError, jwt
from uuid import UUID

from app.database import get_db
from app.config import settings
from app.features.auth.schemas import Token, UserSignup, UserResponse
from app.features.auth.service import AuthService
from app.utils.oauth_cache import (
    is_code_used,
    is_code_processing,
    mark_code_as_processing,
    mark_code_as_used,
    unmark_code_as_processing,
)

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await AuthService.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return UserResponse.model_validate(user)


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    user_data: UserSignup, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """User signup endpoint."""
    # Check if user already exists
    existing_user = await AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await AuthService.create_user(
        db, user_data.name, user_data.email, user_data.password, user_data.role
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """User login endpoint."""
    user = await AuthService.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current user information."""
    return current_user


@router.get("/oauth-config")
async def get_oauth_config() -> dict:
    """
    Debug endpoint to verify OAuth configuration.
    Use this to verify your Google Cloud Console settings match.
    """
    return {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_CALLBACK_URL,
        "redirect_uri_length": len(settings.GOOGLE_CALLBACK_URL),
        "redirect_uri_repr": repr(settings.GOOGLE_CALLBACK_URL),
        "frontend_url": settings.FRONTEND_URL,
        "is_configured": bool(
            settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
        ),
        "expected_google_console_uri": "http://localhost:8000/api/auth/google/callback",
    }


@router.get("/google")
async def google_oauth() -> RedirectResponse:
    """
    Initiate Google OAuth flow.
    Redirects user to Google for authentication.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.",
        )

    # Google OAuth endpoints
    authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"

    # Ensure redirect URI is properly formatted (strip any whitespace)
    redirect_uri = settings.GOOGLE_CALLBACK_URL.strip()

    # Build authorization URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    # Log OAuth initiation (only in development)
    if settings.ENVIRONMENT == "development":
        logger.debug(
            f"OAuth redirect_uri: '{redirect_uri}', " f"length: {len(redirect_uri)}"
        )

    auth_url = f"{authorization_endpoint}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_oauth_callback(
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Handle Google OAuth callback.
    Exchanges authorization code for user info and creates/updates user.
    """
    if error:
        logger.warning(f"OAuth callback error: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )

    if not code:
        logger.warning("OAuth callback called without authorization code")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth not configured")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )

    # CRITICAL: Atomically check and mark code as processing FIRST
    # This must happen before any async operations to prevent race conditions
    # If two requests arrive simultaneously, only one will get True
    # This is the ONLY check needed - it's atomic and handles both used and processing states
    if not mark_code_as_processing(code):
        # Code is already used or being processed by another request
        # This is expected for duplicate requests (browser retries, React StrictMode, etc.)
        # Since the first request already succeeded, just redirect to login without error
        # The user should already be authenticated from the first successful request
        logger.debug(
            f"OAuth callback blocked - duplicate request (code already used/processing): {code[:20]}..."
        )
        # Redirect to login without error - first request already handled authentication
        # Using 303 See Other to prevent browser retry
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login",
            status_code=303,  # See Other - tells browser not to retry
        )

    logger.info(f"Processing OAuth callback with code: {code[:20]}...")

    try:
        # Exchange authorization code for tokens
        oauth_client = AsyncOAuth2Client(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

        token_endpoint = "https://oauth2.googleapis.com/token"
        logger.debug(
            f"Exchanging authorization code for token. "
            f"Redirect URI: {settings.GOOGLE_CALLBACK_URL}"
        )
        # Type ignore: authlib's fetch_token return type is not properly typed
        token_response: dict[str, Any] = await oauth_client.fetch_token(  # type: ignore[assignment]
            token_endpoint,
            code=code,
            redirect_uri=settings.GOOGLE_CALLBACK_URL,
        )

        # Mark code as used immediately after successful exchange
        mark_code_as_used(code)
        logger.info(f"Successfully exchanged authorization code: {code[:20]}...")

        access_token = token_response.get("access_token")
        if not access_token:
            unmark_code_as_processing(code)
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
            )

        # Get user info from Google using httpx directly
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()

        google_id = userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name") or userinfo.get("email", "").split("@")[0]

        if not google_id or not email:
            unmark_code_as_processing(code)
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
            )

        # Create or update user
        user, is_new_user = await AuthService.create_or_update_oauth_user(
            db=db,
            google_id=google_id,
            email=email,
            name=name,
        )

        # Create JWT token
        access_token_expires = timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        jwt_token = AuthService.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )

        # Build redirect URL with token and user info
        user_response = UserResponse.model_validate(user)
        user_json = user_response.model_dump_json()

        redirect_params = {
            "token": jwt_token,
            "user": user_json,
        }

        if is_new_user:
            redirect_params["newUser"] = "true"

        redirect_url = (
            f"{settings.FRONTEND_URL}/api/auth/oauth-callback?{urlencode(redirect_params)}"
        )
        return RedirectResponse(url=redirect_url)

    except OAuthError as e:
        # Handle OAuth-specific errors (like invalid_grant)
        error_description = str(e)
        error_lower = error_description.lower()

        if "invalid_grant" in error_lower:
            # Code was already used or expired - mark as used to prevent retries
            logger.warning(
                f"OAuth invalid_grant error - code already used/expired: {code[:20]}... "
                f"Error: {error_description}. Marking as used to prevent retries."
            )
            mark_code_as_used(code)
            # Don't redirect to error page - just redirect to login
            # The user can try OAuth again if needed
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=oauth_code_invalid"
            )

        # Other OAuth errors - unmark processing but don't mark as used
        # (code might still be valid for retry, but we'll let it expire naturally)
        logger.error(
            f"OAuth error (non-invalid_grant): {error_description}. "
            f"Code: {code[:20]}...",
            exc_info=True
        )
        unmark_code_as_processing(code)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )
    except Exception as e:
        # Generic errors - unmark processing
        logger.error(f"Google OAuth error: {e}", exc_info=True)
        unmark_code_as_processing(code)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )
