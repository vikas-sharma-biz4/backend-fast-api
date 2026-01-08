"""
OAuth authorization code cache to prevent code reuse.
Authorization codes are single-use and expire quickly.
"""
import time
from typing import Dict, Set
from threading import Lock

# In-memory cache for used authorization codes
# Format: {code: timestamp_when_used}
_used_codes: Dict[str, float] = {}
# Track codes currently being processed to prevent race conditions
_processing_codes: Set[str] = set()
_cache_lock = Lock()
_CODE_EXPIRY_SECONDS = 300  # Codes expire after 5 minutes


def is_code_used(code: str) -> bool:
    """
    Check if an authorization code has already been used.

    Args:
        code: Authorization code to check

    Returns:
        True if code was already used, False otherwise
    """
    with _cache_lock:
        # Clean up expired codes
        current_time = time.time()
        expired_codes = [
            c for c, timestamp in _used_codes.items()
            if current_time - timestamp > _CODE_EXPIRY_SECONDS
        ]
        for expired_code in expired_codes:
            del _used_codes[expired_code]

        # Check if code exists
        return code in _used_codes


def is_code_processing(code: str) -> bool:
    """
    Check if an authorization code is currently being processed.

    Args:
        code: Authorization code to check

    Returns:
        True if code is being processed, False otherwise
    """
    with _cache_lock:
        return code in _processing_codes


def mark_code_as_processing(code: str) -> bool:
    """
    Mark an authorization code as being processed.
    Returns False if code is already being processed or used.
    This is atomic - checks and marks in a single locked operation.

    Args:
        code: Authorization code to mark as processing

    Returns:
        True if code can be processed, False if already processing/used
    """
    with _cache_lock:
        # Check both used and processing in one atomic operation
        if code in _used_codes:
            return False
        if code in _processing_codes:
            return False
        # Mark as processing atomically
        _processing_codes.add(code)
        return True


def mark_code_as_used(code: str) -> None:
    """
    Mark an authorization code as used and remove from processing set.

    Args:
        code: Authorization code to mark as used
    """
    with _cache_lock:
        _used_codes[code] = time.time()
        _processing_codes.discard(code)


def unmark_code_as_processing(code: str) -> None:
    """
    Remove code from processing set (if exchange failed for non-reuse reasons).

    Args:
        code: Authorization code to unmark
    """
    with _cache_lock:
        _processing_codes.discard(code)
