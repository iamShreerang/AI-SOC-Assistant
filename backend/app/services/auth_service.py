from datetime import timedelta
from typing import Optional
import secrets

from app.schemas.auth import Token, UserRegister, UserResponse, UserUpdate
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.enums import UserRole

# Mock in-memory user store — replace with DB lookup once schema is ready
_USERS: dict[str, dict] = {
    "analyst": {
        "username": "analyst",
        "hashed_password": hash_password("analyst123"),
        "role": UserRole.ANALYST.value,
        "is_active": True,
    },
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": UserRole.ADMIN.value,
        "is_active": True,
    },
}


def register_user(payload: UserRegister) -> Optional[UserResponse]:
    """Create a new user. Returns None if username is already taken."""
    if payload.username in _USERS:
        return None
    _USERS[payload.username] = {
        "username": payload.username,
        "hashed_password": hash_password(payload.password),
        "role": payload.role.value,
        "is_active": True,
    }
    return UserResponse(username=payload.username, role=payload.role, is_active=True)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = _USERS.get(username)
    if user and user.get("is_active", True) and verify_password(password, user["hashed_password"]):
        return user
    return None


def generate_token(user: dict) -> Token:
    data = {"sub": user["username"], "role": user["role"]}
    return Token(
        access_token=create_access_token(data, expires_delta=timedelta(minutes=15)),
        refresh_token=create_refresh_token(data),
    )


def get_or_create_oauth_user(email: str, provider: str) -> dict:
    """Find existing OAuth user by email or create a new one."""
    username = f"{provider}_{email.split('@')[0]}"
    if username not in _USERS:
        _USERS[username] = {
            "username": username,
            "hashed_password": hash_password(secrets.token_urlsafe(16)),
            "role": UserRole.ANALYST.value,
            "is_active": True,
        }
    return _USERS[username]


def get_all_users() -> list[UserResponse]:
    """Get all users (admin only)."""
    return [
        UserResponse(
            username=user["username"],
            role=user["role"],
            is_active=user.get("is_active", True),
        )
        for user in _USERS.values()
    ]


def get_user_by_username(username: str) -> Optional[UserResponse]:
    """Get user by username."""
    user = _USERS.get(username)
    if not user:
        return None
    return UserResponse(
        username=user["username"],
        role=user["role"],
        is_active=user.get("is_active", True),
    )


def update_user(username: str, payload: UserUpdate) -> Optional[UserResponse]:
    """Update user details (admin only)."""
    user = _USERS.get(username)
    if not user:
        return None
    
    if payload.role:
        user["role"] = payload.role.value
    if payload.is_active is not None:
        user["is_active"] = payload.is_active
    
    return UserResponse(
        username=user["username"],
        role=user["role"],
        is_active=user.get("is_active", True),
    )


def delete_user(username: str) -> bool:
    """Delete user (admin only)."""
    if username in ["analyst", "admin"]:
        return False  # Prevent deleting default users
    if username in _USERS:
        del _USERS[username]
        return True
    return False
