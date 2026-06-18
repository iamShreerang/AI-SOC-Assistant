from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.services.auth_service import authenticate_user, generate_token, register_user
from app.utils.security import get_current_active_user, TokenData

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
Create a new user account with a hashed password.

**Roles:**
- `analyst` (default) — can read/write logs, alerts, and incidents
- `admin` — all analyst permissions plus future admin capabilities

**Notes:**
- Usernames are unique. A 409 is returned if the username is already taken.
- Passwords are hashed with bcrypt before storage; plain-text is never persisted.
""",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Username already taken"},
        422: {"description": "Validation error — missing or invalid fields"},
    },
)
def register(payload: UserRegister):
    user = register_user(payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and obtain a JWT token",
    description="""
Authenticate with username and password.

On success, returns a **JWT bearer token** valid for **15 minutes**.

**How to use the token:**
```
Authorization: Bearer <access_token>
```

Include this header on every request to a protected endpoint.
Returns `401 Unauthorized` if credentials are invalid.
""",
    responses={
        200: {"description": "Authenticated — JWT token returned"},
        401: {"description": "Invalid username or password"},
        422: {"description": "Validation error — missing fields"},
    },
)
def login(credentials: UserLogin):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return generate_token(user)


@router.get(
    "/users/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
    description="""
Returns the username and role of the currently authenticated caller.

Useful for verifying that a token is valid and inspecting the caller's role.
Requires a valid `Authorization: Bearer <token>` header.
""",
    responses={
        200: {"description": "Caller identity returned"},
        401: {"description": "Missing, invalid, or expired token"},
    },
)
def me(current_user: TokenData = Depends(get_current_active_user)):
    return UserResponse(username=current_user.username, role=current_user.role)
