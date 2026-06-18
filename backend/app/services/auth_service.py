from datetime import timedelta
from typing import Optional

from app.schemas.auth import Token, UserRegister, UserResponse
from app.utils.security import hash_password, verify_password, create_access_token

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
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=15),
    )
    return Token(access_token=token)
