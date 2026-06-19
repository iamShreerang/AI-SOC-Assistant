from datetime import timedelta
from typing import Optional
import secrets

from app.schemas.auth import Token, UserRegister, UserResponse
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token

# Mock in-memory user store — replace with DB lookup once schema is ready
_USERS: dict[str, dict] = {
    "analyst": {
        "username": "analyst",
        "hashed_password": hash_password("analyst123"),
        "role": "analyst",
    },
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
    },
}


def register_user(payload: UserRegister) -> Optional[UserResponse]:
    """Create a new user. Returns None if username is already taken."""
    if payload.username in _USERS:
        return None
    _USERS[payload.username] = {
        "username": payload.username,
        "hashed_password": hash_password(payload.password),
        "role": payload.role,
    }
    return UserResponse(username=payload.username, role=payload.role)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = _USERS.get(username)
    if user and verify_password(password, user["hashed_password"]):
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
            "role": "analyst",
        }
    return _USERS[username]
