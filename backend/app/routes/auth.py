from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse, UserUpdate
from app.services import db_auth_service, db_audit_service
from app.database import get_db
from app.utils.security import (
    get_current_active_user,
    TokenData,
    decode_refresh_token,
    blacklist_token,
    oauth2_scheme,
    require_role,
)
from app.utils.password_validator import validate_password_simple
from app.utils.oauth import oauth
from app.utils.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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

**Password Requirements:**
- Minimum 8 characters

**Notes:**
- Usernames are unique. A 409 is returned if the username is already taken.
- Passwords are hashed with bcrypt before storage; plain-text is never persisted.
""",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Password does not meet requirements"},
        409: {"description": "Username already taken"},
        422: {"description": "Validation error — missing or invalid fields"},
    },
)
@limiter.limit("5/minute")
def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)):
    # Validate password strength
    is_valid, error_msg = validate_password_simple(payload.password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    user = db_auth_service.register_user(db, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    
    # Audit log
    db_audit_service.log_action(
        db,
        username="system",
        action="user.register",
        resource_type="user",
        resource_id=payload.username,
        details=f"New user registered: {payload.username} (role: {payload.role.value})",
    )
    
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
@limiter.limit("10/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    user = db_auth_service.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return db_auth_service.generate_token(user)


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
    return UserResponse(username=current_user.username, role=current_user.role, is_active=True)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token, summary="Refresh access token")
@limiter.limit("10/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_refresh_token(payload.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user = db_auth_service.get_user_by_username_internal(db, token_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return db_auth_service.generate_token(user)


@router.post("/logout", status_code=200, summary="Logout and revoke token")
def logout(token: str = Depends(oauth2_scheme)):
    blacklist_token(token)
    return {"detail": "Successfully logged out"}


# ── OAuth Routes ──────────────────────────────────────────────────────────────

@router.get("/login/google", summary="Redirect to Google OAuth")
async def login_google(request: Request):
    redirect_uri = str(request.url_for("auth_google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", name="auth_google_callback", summary="Google OAuth callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google")
    user = db_auth_service.get_or_create_oauth_user(db, user_info["email"], "google")
    token_data = db_auth_service.generate_token(user)
    
    # Redirect to frontend with tokens as query parameters
    redirect_url = f"{settings.frontend_url}/auth/callback?access_token={token_data.access_token}&refresh_token={token_data.refresh_token}"
    return RedirectResponse(url=redirect_url)


@router.get("/login/github", summary="Redirect to GitHub OAuth")
async def login_github(request: Request):
    redirect_uri = str(request.url_for("auth_github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/callback/github", name="auth_github_callback", summary="GitHub OAuth callback")
async def auth_github_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("https://api.github.com/user/emails", token=token)
    emails = resp.json()
    primary_email = next((e["email"] for e in emails if e.get("primary")), None)
    if not primary_email:
        raise HTTPException(status_code=400, detail="Could not fetch email from GitHub")
    user = db_auth_service.get_or_create_oauth_user(db, primary_email, "github")
    token_data = db_auth_service.generate_token(user)
    
    # Redirect to frontend with tokens as query parameters
    redirect_url = f"{settings.frontend_url}/auth/callback?access_token={token_data.access_token}&refresh_token={token_data.refresh_token}"
    return RedirectResponse(url=redirect_url)


# ── Admin User Management Routes ──────────────────────────────────────────────

@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
    description="Returns a list of all registered users with their roles and status.",
    responses={
        200: {"description": "List of users"},
        403: {"description": "Requires admin role"},
    },
)
def list_users(db: Session = Depends(get_db), _admin=Depends(require_role("admin"))):
    return db_auth_service.get_all_users(db)


@router.get(
    "/users/{username}",
    response_model=UserResponse,
    summary="Get user by username (admin only)",
    description="Returns details of a specific user.",
    responses={
        200: {"description": "User details"},
        403: {"description": "Requires admin role"},
        404: {"description": "User not found"},
    },
)
def get_user(username: str, db: Session = Depends(get_db), _admin=Depends(require_role("admin"))):
    user = db_auth_service.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/users/{username}",
    response_model=UserResponse,
    summary="Update user (admin only)",
    description="Update user role or active status.",
    responses={
        200: {"description": "User updated"},
        403: {"description": "Requires admin role"},
        404: {"description": "User not found"},
    },
)
def update_user_endpoint(
    username: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role("admin"))
):
    user = db_auth_service.update_user(db, username, payload)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Audit log
    db_audit_service.log_action(
        db,
        username=current_user.username,
        action="user.update",
        resource_type="user",
        resource_id=username,
        details=f"Updated user: role={payload.role.value if payload.role else 'unchanged'}, active={payload.is_active if payload.is_active is not None else 'unchanged'}",
    )
    
    return user


@router.delete(
    "/users/{username}",
    status_code=200,
    summary="Delete user (admin only)",
    description="Remove a user from the system. Cannot delete default analyst/admin users.",
    responses={
        200: {"description": "User deleted"},
        403: {"description": "Requires admin role or cannot delete default users"},
        404: {"description": "User not found"},
    },
)
def delete_user_endpoint(
    username: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role("admin"))
):
    success = db_auth_service.delete_user(db, username)
    if not success:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete default users or user not found",
        )
    
    # Audit log
    db_audit_service.log_action(
        db,
        username=current_user.username,
        action="user.delete",
        resource_type="user",
        resource_id=username,
        details=f"Deleted user: {username}",
    )
    
    return {"detail": f"User '{username}' deleted successfully"}
