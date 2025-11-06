"""
Admin privilege consistency tests (T311, FR-118)

Tests that all admin endpoints use get_current_admin() dependency
and correctly enforce admin-only access.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_db
from app.models.user import User
from app.models.session import Session
from app.main import app
import bcrypt


# Test database setup
@pytest.fixture(scope="function")
async def test_db():
    """Create a clean test database for each test"""
    # Use SQLite in-memory for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create async session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield async_session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def regular_user_with_session(test_db):
    """Create a regular (non-admin) user with active session"""
    async with test_db() as session:
        # Create regular user
        password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt(rounds=12)).decode()
        user = User(
            id=uuid4(),
            username="regular_user",
            password_hash=password_hash,
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)

        # Create active session (expires in 30 minutes)
        session_token = "regular_session_token_" + str(uuid4())
        user_session = Session(
            id=uuid4(),
            user_id=user.id,
            session_token=session_token,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        session.add(user_session)

        await session.commit()
        await session.refresh(user)
        await session.refresh(user_session)

        return {
            "user": user,
            "session_token": session_token,
        }


@pytest.fixture
async def admin_user_with_session(test_db):
    """Create an admin user with active session"""
    async with test_db() as session:
        # Create admin user
        password_hash = bcrypt.hashpw("adminpass123".encode(), bcrypt.gensalt(rounds=12)).decode()
        user = User(
            id=uuid4(),
            username="admin_user",
            password_hash=password_hash,
            is_admin=True,  # Admin flag set to True
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)

        # Create active session (expires in 30 minutes)
        session_token = "admin_session_token_" + str(uuid4())
        user_session = Session(
            id=uuid4(),
            user_id=user.id,
            session_token=session_token,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        session.add(user_session)

        await session.commit()
        await session.refresh(user)
        await session.refresh(user_session)

        return {
            "user": user,
            "session_token": session_token,
        }


@pytest.fixture
async def async_client(test_db):
    """Create an async test client with database override"""
    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Test cases

@pytest.mark.asyncio
async def test_non_admin_user_accessing_admin_endpoint_returns_403(
    async_client,
    regular_user_with_session,
):
    """
    Test that non-admin user accessing /admin/users returns 403 Forbidden.

    Verifies FR-118: Admin privilege enforcement through get_current_admin() dependency.
    """
    session_token = regular_user_with_session["session_token"]

    # Try to access admin endpoint with regular user session
    response = await async_client.get(
        "/api/v1/admin/users",
        cookies={"session_token": session_token},
    )

    # Should return 403 Forbidden
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    # Check error message in Korean (T311, FR-118)
    error_detail = response.json().get("detail", "")
    assert error_detail == "관리자 권한이 필요합니다.", (
        f"Expected Korean error message '관리자 권한이 필요합니다.', got '{error_detail}'"
    )


@pytest.mark.asyncio
async def test_admin_user_accessing_admin_endpoint_returns_200(
    async_client,
    admin_user_with_session,
):
    """
    Test that admin user accessing /admin/users returns 200 OK.

    Verifies FR-118: Admin users can access admin endpoints.
    """
    session_token = admin_user_with_session["session_token"]

    # Access admin endpoint with admin user session
    response = await async_client.get(
        "/api/v1/admin/users",
        cookies={"session_token": session_token},
    )

    # Should return 200 OK
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Response should contain users list
    data = response.json()
    assert "users" in data, "Response should contain 'users' field"
    assert "total" in data, "Response should contain 'total' field"
    assert isinstance(data["users"], list), "users should be a list"


@pytest.mark.asyncio
async def test_unauthenticated_user_accessing_admin_endpoint_returns_401(
    async_client,
):
    """
    Test that unauthenticated user accessing /admin/users returns 401 Unauthorized.

    Verifies authentication is required before admin privilege check.
    """
    # Try to access admin endpoint without session token
    response = await async_client.get("/api/v1/admin/users")

    # Should return 401 Unauthorized (authentication required)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    error_detail = response.json().get("detail", "")
    assert error_detail, "Error message should not be empty"


@pytest.mark.asyncio
async def test_admin_user_can_create_new_user(
    async_client,
    admin_user_with_session,
):
    """
    Test that admin user can create new users via POST /admin/users.

    Verifies FR-033: Admin user management capabilities.
    """
    session_token = admin_user_with_session["session_token"]

    # Create new user
    response = await async_client.post(
        "/api/v1/admin/users",
        cookies={"session_token": session_token},
        json={
            "username": "new_test_user",
            "password": "securepass123",
            "is_admin": False,
        },
    )

    # Should return 201 Created
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    # Response should contain new user data
    data = response.json()
    assert data["username"] == "new_test_user"
    assert data["is_admin"] is False


@pytest.mark.asyncio
async def test_regular_user_cannot_create_new_user(
    async_client,
    regular_user_with_session,
):
    """
    Test that regular user cannot create new users via POST /admin/users.

    Verifies FR-118: Admin privilege enforcement on user creation.
    """
    session_token = regular_user_with_session["session_token"]

    # Try to create new user as regular user
    response = await async_client.post(
        "/api/v1/admin/users",
        cookies={"session_token": session_token},
        json={
            "username": "unauthorized_user",
            "password": "password123",
            "is_admin": False,
        },
    )

    # Should return 403 Forbidden
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    # Verify Korean error message (T311)
    error_detail = response.json().get("detail", "")
    assert error_detail == "관리자 권한이 필요합니다.", (
        f"Expected Korean error message, got '{error_detail}'"
    )


@pytest.mark.asyncio
async def test_admin_endpoints_use_get_current_admin_dependency():
    """
    Test that all admin endpoints use get_current_admin() dependency.

    This is a code inspection test to ensure consistency (FR-118).
    """
    from app.api.v1.admin import router
    from app.api.deps import get_current_admin
    import inspect

    # Get all routes in admin router
    for route in router.routes:
        if hasattr(route, "dependant"):
            # Check if get_current_admin is in dependencies
            dependencies = route.dependant.dependencies
            dependency_calls = [dep.call for dep in dependencies]

            # At least one dependency should be get_current_admin
            has_admin_check = any(
                callable(dep) and (dep == get_current_admin or dep.__name__ == "get_current_admin")
                for dep in dependency_calls
            )

            # Admin routes should use get_current_admin
            # (except for sub-routers like /agents which have their own checks)
            if not route.path.startswith("/agents"):
                assert has_admin_check, f"Route {route.path} should use get_current_admin dependency"
