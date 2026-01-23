"""
Authentication routes.
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
from urllib.parse import urlencode

from app.database import get_db
from app.schemas.auth import Token, UserSignup, UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token,
    get_user_by_id,
)
from app.services.oauth_service import create_or_update_oauth_user
from app.models.user import User
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get current authenticated user."""
    from jose import JWTError, jwt
    from uuid import UUID

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return UserResponse.model_validate(user)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: AsyncSession = Depends(get_db)):
    """User signup endpoint."""
    from app.services.auth_service import get_user_by_email

    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await create_user(db, user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """User login endpoint."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.get("/oauth-config")
async def get_oauth_config():
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
        "is_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        "expected_google_console_uri": "http://localhost:8000/api/auth/google/callback",
    }


@router.get("/google")
async def google_oauth():
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
            f"OAuth redirect_uri: '{redirect_uri}', "
            f"length: {len(redirect_uri)}"
        )

    auth_url = f"{authorization_endpoint}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_oauth_callback(
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for user info and creates/updates user.
    """
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )

    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )

    try:
        # Exchange authorization code for tokens
        oauth_client = AsyncOAuth2Client(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

        token_endpoint = "https://oauth2.googleapis.com/token"
        # Type ignore: authlib's fetch_token return type is not properly typed
        token_response: dict[str, Any] = await oauth_client.fetch_token(  # type: ignore[assignment]
            token_endpoint,
            code=code,
            redirect_uri=settings.GOOGLE_CALLBACK_URL,
        )

        access_token = token_response.get("access_token")
        if not access_token:
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
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
            )

        # Create or update user
        user, is_new_user = await create_or_update_oauth_user(
            db=db,
            google_id=google_id,
            email=email,
            name=name,
        )

        # Create JWT token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
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

        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?{urlencode(redirect_params)}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"Google OAuth error: {e}", exc_info=True)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )
