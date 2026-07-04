"""
API Dependencies
================
Dependencies untuk API (auth, DB session).
"""

from backend.config import decode_token
from backend.repositories import UserRepository
from typing import Optional, Dict


def get_current_user(token: str) -> Optional[Dict]:
    """Get current user dari JWT token."""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id:
            return UserRepository.get_by_id(user_id)
    except:
        pass
    return None


def require_auth(token: str) -> Dict:
    """Require authentication. Raise error jika tidak valid."""
    user = get_current_user(token)
    if not user:
        raise ValueError("Authentication required")
    return user