from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.schemas.auth import TokenData
from app.utils.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.refresh_secret_key, algorithm=settings.algorithm)


def decode_refresh_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.refresh_secret_key, algorithms=settings.allowed_algorithms)
        if payload.get("type") != "refresh":
            return None
        username = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username, role=payload.get("role"))
    except jwt.PyJWTError:
        return None


def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=settings.allowed_algorithms)
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username, role=payload.get("role"))
    except jwt.PyJWTError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    token_data = decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    return current_user
