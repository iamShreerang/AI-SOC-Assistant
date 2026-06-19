from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.services.auth_service import authenticate_user, generate_token, register_user, get_or_create_oauth_user, _USERS
from app.utils.security import get_current_active_user, TokenData, decode_refresh_token
from app.utils.oauth import oauth
from app.utils.config import settings

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


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token, summary="Refresh access token")
def refresh(payload: RefreshRequest):
    token_data = decode_refresh_token(payload.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user = _USERS.get(token_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return generate_token(user)


# ── OAuth Routes ──────────────────────────────────────────────────────────────

@router.get("/login/google", summary="Redirect to Google OAuth")
async def login_google(request: Request):
    redirect_uri = str(request.url_for("auth_google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", name="auth_google_callback", summary="Google OAuth callback")
async def auth_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google")
    user = get_or_create_oauth_user(user_info["email"], "google")
    return generate_token(user)


@router.get("/login/github", summary="Redirect to GitHub OAuth")
async def login_github(request: Request):
    redirect_uri = str(request.url_for("auth_github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/callback/github", name="auth_github_callback", summary="GitHub OAuth callback")
async def auth_github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("https://api.github.com/user/emails", token=token)
    emails = resp.json()
    primary_email = next((e["email"] for e in emails if e.get("primary")), None)
    if not primary_email:
        raise HTTPException(status_code=400, detail="Could not fetch email from GitHub")
    user = get_or_create_oauth_user(primary_email, "github")
    return generate_token(user)
