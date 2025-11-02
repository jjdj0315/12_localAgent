"""API dependencies for authentication and authorization"""

from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service


async def get_current_user(
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from session token.

    Supports both cookie-based and header-based authentication.

    Args:
        session_token: Session token from cookie
        authorization: Authorization header (Bearer token)
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If not authenticated
    """
    # Try to get token from Authorization header first (for API clients)
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    # Fallback to cookie (for browser clients)
    elif session_token:
        token = session_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )

    # Get session
    session = await auth_service.get_session_by_token(db, token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        )

    # Get user
    user = await auth_service.get_user_by_id(db, session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        )

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and verify admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user (if admin)

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource.",
        )

    return current_user
