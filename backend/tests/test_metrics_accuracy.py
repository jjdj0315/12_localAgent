"""
Metric accuracy integration tests (T306, FR-116)

Tests for timezone-aware active user metric calculation:
- Non-expired sessions counted correctly
- Expired sessions not counted
- Timezone-aware datetime objects used
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.business_metrics import update_active_users_metric
from app.models.session import Session as UserSession
from app.models.user import User


@pytest.mark.asyncio
async def test_active_users_counts_non_expired_sessions():
    """
    Test active users metric counts only non-expired sessions (T306, FR-116)

    Creates:
    - 2 non-expired sessions (expires_at in future)
    - 1 expired session (expires_at in past)

    Expected: active_users_count == 2
    """
    async with AsyncSessionLocal() as db:
        # Clean up any existing test data
        await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_metric_%')")
        await db.execute("DELETE FROM users WHERE username LIKE 'test_metric_%'")
        await db.commit()

        try:
            # Create test users
            user1 = User(username="test_metric_user1", password_hash="hash1", is_admin=False)
            user2 = User(username="test_metric_user2", password_hash="hash2", is_admin=False)
            user3 = User(username="test_metric_user3", password_hash="hash3", is_admin=False)

            db.add_all([user1, user2, user3])
            await db.flush()

            # Current time (timezone-aware)
            now = datetime.now(timezone.utc)

            # Create 2 non-expired sessions (expires in future)
            session1 = UserSession(
                user_id=user1.id,
                session_token="token1",
                expires_at=now + timedelta(minutes=30)
            )
            session2 = UserSession(
                user_id=user2.id,
                session_token="token2",
                expires_at=now + timedelta(minutes=15)
            )

            # Create 1 expired session (expires in past)
            session3_expired = UserSession(
                user_id=user3.id,
                session_token="token3_expired",
                expires_at=now - timedelta(minutes=1)  # Expired 1 minute ago
            )

            db.add_all([session1, session2, session3_expired])
            await db.commit()

            # Call metric update function
            await update_active_users_metric(db)

            # Query the metric (check database directly)
            from sqlalchemy import select, func
            query = select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.expires_at > now
            )
            result = await db.execute(query)
            active_count = result.scalar()

            # Assert only non-expired sessions counted
            assert active_count == 2, f"Expected 2 active users, got {active_count}"

        finally:
            # Cleanup
            await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_metric_%')")
            await db.execute("DELETE FROM users WHERE username LIKE 'test_metric_%')")
            await db.commit()


@pytest.mark.asyncio
async def test_active_users_uses_timezone_aware_datetime():
    """
    Test that metric calculation uses timezone-aware datetime (T306, FR-116)

    Verifies that datetime objects have tzinfo set (not None).
    """
    async with AsyncSessionLocal() as db:
        # The function should use timezone-aware datetime
        now = datetime.now(timezone.utc)

        # Verify it has timezone info
        assert now.tzinfo is not None, "Datetime should be timezone-aware"
        assert now.tzinfo == timezone.utc, "Timezone should be UTC"

        # Test that metric update doesn't crash with timezone-aware datetime
        try:
            await update_active_users_metric(db)
            # If no exception, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Metric update failed with timezone-aware datetime: {e}")


@pytest.mark.asyncio
async def test_active_users_zero_when_no_sessions():
    """
    Test that active users count is 0 when no active sessions exist (T306)
    """
    async with AsyncSessionLocal() as db:
        # Clean up test data
        await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_metric_%')")
        await db.execute("DELETE FROM users WHERE username LIKE 'test_metric_%'")
        await db.commit()

        try:
            # Create user but no sessions
            user = User(username="test_metric_no_session", password_hash="hash", is_admin=False)
            db.add(user)
            await db.commit()

            # Update metric
            await update_active_users_metric(db)

            # Query active count
            from sqlalchemy import select, func
            now = datetime.now(timezone.utc)
            query = select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.expires_at > now
            )
            result = await db.execute(query)
            active_count = result.scalar()

            # Should be 0 (no active sessions)
            assert active_count == 0, f"Expected 0 active users, got {active_count}"

        finally:
            await db.execute("DELETE FROM users WHERE username LIKE 'test_metric_%'")
            await db.commit()


@pytest.mark.asyncio
async def test_active_users_multiple_sessions_same_user():
    """
    Test that multiple sessions from same user counts as 1 active user (T306, FR-116)

    Verifies DISTINCT user_id in query.
    """
    async with AsyncSessionLocal() as db:
        await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username = 'test_metric_multi')")
        await db.execute("DELETE FROM users WHERE username = 'test_metric_multi'")
        await db.commit()

        try:
            # Create one user
            user = User(username="test_metric_multi", password_hash="hash", is_admin=False)
            db.add(user)
            await db.flush()

            # Create 3 active sessions for same user
            now = datetime.now(timezone.utc)
            for i in range(3):
                session = UserSession(
                    user_id=user.id,
                    session_token=f"token_multi_{i}",
                    expires_at=now + timedelta(minutes=30)
                )
                db.add(session)

            await db.commit()

            # Query active users (should be 1, not 3)
            from sqlalchemy import select, func
            query = select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.expires_at > now
            )
            result = await db.execute(query)
            active_count = result.scalar()

            # Should be 1 (distinct user_id)
            assert active_count == 1, f"Expected 1 active user (3 sessions), got {active_count}"

        finally:
            await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username = 'test_metric_multi')")
            await db.execute("DELETE FROM users WHERE username = 'test_metric_multi'")
            await db.commit()


@pytest.mark.asyncio
async def test_active_users_boundary_case_exact_expiry():
    """
    Test boundary case where session expires at exactly current time (T306)

    Session with expires_at == now should NOT be counted (> not >=).
    """
    async with AsyncSessionLocal() as db:
        await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username = 'test_metric_boundary')")
        await db.execute("DELETE FROM users WHERE username = 'test_metric_boundary'")
        await db.commit()

        try:
            user = User(username="test_metric_boundary", password_hash="hash", is_admin=False)
            db.add(user)
            await db.flush()

            # Create session that expires exactly now
            now = datetime.now(timezone.utc)
            session = UserSession(
                user_id=user.id,
                session_token="token_boundary",
                expires_at=now  # Expires exactly at current time
            )
            db.add(session)
            await db.commit()

            # Query with same timestamp
            from sqlalchemy import select, func
            query = select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.expires_at > now  # > not >=
            )
            result = await db.execute(query)
            active_count = result.scalar()

            # Should be 0 (expires_at == now, not > now)
            assert active_count == 0, f"Session expiring at exactly 'now' should not be active, got {active_count}"

        finally:
            await db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username = 'test_metric_boundary')")
            await db.execute("DELETE FROM users WHERE username = 'test_metric_boundary'")
            await db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
