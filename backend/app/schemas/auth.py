from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class UserRegister(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Register an analyst",
                    "value": {"username": "jsmith", "password": "S3cur3P@ss!", "role": "analyst"},
                },
                {
                    "summary": "Register an admin",
                    "value": {"username": "soc_admin", "password": "Adm1nP@ss!", "role": "admin"},
                },
            ]
        }
    )

    username: str = Field(..., min_length=3, max_length=50, description="Unique login handle")
    password: str = Field(..., min_length=1, description="Plain-text password (hashed before storage)")
    role: str = Field("analyst", description="User role: `analyst` or `admin`")


class UserLogin(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Analyst login",
                    "value": {"username": "analyst", "password": "analyst123"},
                }
            ]
        }
    )

    username: str = Field(..., description="Registered username")
    password: str = Field(..., description="Account password")


class UserResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"username": "jsmith", "role": "analyst"}]
        }
    )

    username: str
    role: str


class Token(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
            ]
        }
    )

    access_token: str = Field(..., description="Signed JWT — include as `Authorization: Bearer <token>`")
    refresh_token: str = Field(..., description="Refresh token — use at `POST /auth/refresh` to get a new access token")
    token_type: str = Field("bearer", description="Always `bearer`")


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
