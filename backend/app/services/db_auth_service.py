"""Authentication service with PostgreSQL backend."""

from datetime import timedelta
from typing import Optional
import secrets
from sqlalchemy.orm import Session

from app.schemas.auth import Token, UserRegister, UserResponse, UserUpdate
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.enums import UserRole
from app.models.database import User


def register_user(db: Session, payload: UserRegister) -> Optional[UserResponse]:
    """Create a new user. Returns None if username is already taken."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        return None
    
    # Create new user
    db_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        username=db_user.username,
        role=db_user.role,
        is_active=db_user.is_active,
    )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user and return user object if valid."""
    user = db.query(User).filter(User.username == username).first()
    if user and user.is_active and verify_password(password, user.hashed_password):
        return user
    return None


def generate_token(user: User) -> Token:
    """Generate JWT access and refresh tokens for user."""
    data = {"sub": user.username, "role": user.role.value}
    return Token(
        access_token=create_access_token(data, expires_delta=timedelta(minutes=15)),
        refresh_token=create_refresh_token(data),
    )


def get_or_create_oauth_user(db: Session, email: str, provider: str) -> User:
    """Find existing OAuth user by username or create a new one."""
    username = f"{provider}_{email.split('@')[0]}"
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            username=username,
            hashed_password=hash_password(secrets.token_urlsafe(16)),
            role=UserRole.ANALYST,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


def get_all_users(db: Session) -> list[UserResponse]:
    """Get all users (admin only)."""
    users = db.query(User).all()
    return [
        UserResponse(
            username=user.username,
            role=user.role,
            is_active=user.is_active,
        )
        for user in users
    ]


def get_user_by_username(db: Session, username: str) -> Optional[UserResponse]:
    """Get user by username."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    return UserResponse(
        username=user.username,
        role=user.role,
        is_active=user.is_active,
    )


def get_user_by_username_internal(db: Session, username: str) -> Optional[User]:
    """Get user ORM object by username (for internal use)."""
    return db.query(User).filter(User.username == username).first()


def update_user(db: Session, username: str, payload: UserUpdate) -> Optional[UserResponse]:
    """Update user details (admin only)."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    if payload.role:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        username=user.username,
        role=user.role,
        is_active=user.is_active,
    )


def delete_user(db: Session, username: str) -> bool:
    """Delete user (admin only)."""
    # Prevent deleting default users
    if username in ["analyst", "admin"]:
        return False
    
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    
    return False


def create_default_users(db: Session):
    """Create default analyst and admin users if they don't exist."""
    default_users = [
        {
            "username": "analyst",
            "password": "analyst123",
            "role": UserRole.ANALYST,
        },
        {
            "username": "admin",
            "password": "admin123",
            "role": UserRole.ADMIN,
        },
    ]
    
    for user_data in default_users:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            db_user = User(
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
            )
            db.add(db_user)
    
    db.commit()
