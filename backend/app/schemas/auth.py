from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.schemas.enums import UserRole


class UserRegister(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "analyst",
                "password": "analyst123",
                "role": "analyst",
            }
        }
    )

    username: str = Field(..., min_length=3, max_length=50, description="Unique login handle")
    password: str = Field(..., min_length=1, description="Plain-text password (hashed before storage)")
    role: UserRole = Field(UserRole.ANALYST, description="User role: `analyst` or `admin`")


class UserLogin(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "analyst",
                "password": "analyst123",
            }
        }
    )

    username: str = Field(..., description="Registered username")
    password: str = Field(..., description="Account password")


class UserResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"username": "analyst", "role": "analyst", "is_active": True}
        }
    )

    username: str
    role: UserRole
    is_active: bool = True


class Token(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )

    access_token: str = Field(..., description="Signed JWT — include as `Authorization: Bearer <token>`")
    refresh_token: str = Field(..., description="Refresh token — use at `POST /auth/refresh` to get a new access token")
    token_type: str = Field("bearer", description="Always `bearer`")


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for admin to update user details."""
    role: Optional[UserRole] = Field(None, description="New role: `analyst` or `admin`")
    is_active: Optional[bool] = Field(None, description="Active status")
