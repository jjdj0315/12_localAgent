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

    **Data Isolation Enforcement (FR-032, FR-122)**:

    This dependency is the cornerstone of data isolation in our system. By requiring
    all user-scoped API endpoints to use this dependency, we ensure that:

    1. **Automatic user_id filtering**: Every route using this dependency has access
       to the authenticated user, enabling automatic filtering of queries by user_id.

    2. **Dependency-level isolation** (FR-122 Option B): We chose dependency-level
       isolation over middleware-based isolation because:
       - More explicit: Each endpoint clearly declares its authentication requirement
       - More flexible: Endpoints can choose different authentication strategies
       - Better performance: No middleware overhead for public/exempt endpoints
       - Easier testing: Dependencies can be easily mocked in tests

    3. **Example routes enforcing user_id filtering**:
       - GET /api/v1/conversations: Returns only current_user.id conversations
       - GET /api/v1/conversations/{id}: Verifies conversation.user_id == current_user.id
       - DELETE /api/v1/conversations/{id}: Verifies conversation.user_id == current_user.id
       - GET /api/v1/documents: Returns only documents from current_user's conversations
       - POST /api/v1/chat/{conversation_id}: Verifies conversation.user_id == current_user.id

    4. **Security guarantee**: Users CANNOT access data belonging to other users,
       even if they know the UUID of another user's conversation/document.

    **Implementation pattern**:
    ```python
    @router.get("/conversations/{conversation_id}")
    async def get_conversation(
        conversation_id: UUID,
        current_user: User = Depends(get_current_user),  # <-- Enforces authentication
        db: AsyncSession = Depends(get_db)
    ):
        # Query with user_id filter
        conversation = await db.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return conversation
    ```

    **References**:
    - FR-032: "Users can only see/modify their own conversations and documents"
    - FR-122: Data isolation implementation decision (Option B: dependency-level)
    - SC-005: Data isolation success criteria (no cross-user data access)

    Args:
        session_token: Session token from cookie
        authorization: Authorization header (Bearer token)
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If not authenticated (401 Unauthorized)
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
    Get current user and verify admin privileges (FR-118).

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
            detail="관리자 권한이 필요합니다.",  # Korean error message (T311)
        )

    return current_user
