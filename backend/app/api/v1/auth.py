"""Authentication endpoints"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint.

    Authenticates user and creates a session.
    Sets session token as HTTP-only cookie.
    """
    # Authenticate user
    user = await auth_service.authenticate_user(
        db, credentials.username, credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 이름 또는 비밀번호가 올바르지 않습니다.",  # T314: Korean message
        )

    # Create session
    session = await auth_service.create_session(db, user.id)

    # Update last login
    await auth_service.update_last_login(db, user.id)

    # Set session cookie with environment-based security settings (FR-112)
    # httponly=True prevents XSS attacks (session token never exposed to JavaScript)
    # secure and samesite dynamically set based on ENVIRONMENT variable
    response.set_cookie(
        key="session_token",
        value=session.session_token,
        httponly=True,  # Prevent JavaScript access (XSS protection)
        secure=settings.cookie_secure,  # True in production, False in development
        samesite=settings.cookie_samesite,  # strict in production, lax in development
        max_age=settings.SESSION_TIMEOUT_MINUTES * 60,  # Match session timeout
        path="/",
        domain=None,  # Let browser set domain
    )

    return LoginResponse(
        user_id=user.id,
        username=user.username,
        is_admin=user.is_admin
    )


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    User logout endpoint.

    Invalidates session and clears cookie.
    """
    if session_token:
        await auth_service.delete_session(db, session_token)

    # Clear cookie
    response.delete_cookie(key="session_token")

    return {"message": "로그아웃 성공"}  # T314: Korean message


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile.

    Returns authenticated user's information.
    """
    return UserProfile.from_orm(current_user)
