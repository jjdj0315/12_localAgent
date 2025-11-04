"""
FR-031 Account Lockout Feature Test

Tests:
1. Create test user
2. Fail login 5 times -> account locked
3. Verify lockout status
4. Admin manually unlocks account
5. Verify unlock status
"""
import asyncio
from datetime import datetime, timezone
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.services.auth_service import auth_service, MAX_FAILED_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES
from app.core.security import hash_password

# Database connection
DATABASE_URL = "postgresql+asyncpg://llm_app:TestPassword123!@localhost:5432/llm_webapp"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def cleanup_test_user(db: AsyncSession):
    """Remove test user if exists"""
    result = await db.execute(select(User).where(User.username == "test_lockout"))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
        print("[OK] Cleaned up existing test user")


async def create_test_user(db: AsyncSession) -> User:
    """Create test user for lockout testing"""
    user = User(
        username="test_lockout",
        password_hash=hash_password("correct_password"),
        email="test@example.com",
        is_admin=False,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"[OK] Created test user: {user.username} (id={user.id})")
    return user


async def test_failed_logins(db: AsyncSession):
    """Test: 5 failed login attempts should lock account"""
    print(f"\n=== Test 1: Failed Login Attempts (Max: {MAX_FAILED_LOGIN_ATTEMPTS}) ===")

    # Attempt 1-4: Should fail but not lock
    for i in range(1, MAX_FAILED_LOGIN_ATTEMPTS):
        user = await auth_service.authenticate_user(db, "test_lockout", "wrong_password")
        assert user is None, f"Attempt {i} should fail"

        # Check user state
        result = await db.execute(select(User).where(User.username == "test_lockout"))
        check_user = result.scalar_one()
        print(f"  Attempt {i}: failed_attempts={check_user.failed_login_attempts}, locked={check_user.is_locked}")

        assert check_user.failed_login_attempts == i
        assert check_user.is_locked == False

    # Attempt 5: Should lock account
    user = await auth_service.authenticate_user(db, "test_lockout", "wrong_password")
    assert user is None, "Attempt 5 should fail"

    result = await db.execute(select(User).where(User.username == "test_lockout"))
    locked_user = result.scalar_one()

    print(f"  Attempt {MAX_FAILED_LOGIN_ATTEMPTS}: failed_attempts={locked_user.failed_login_attempts}, locked={locked_user.is_locked}")
    print(f"  locked_until: {locked_user.locked_until}")

    assert locked_user.is_locked == True, "Account should be locked"
    assert locked_user.locked_until is not None, "Lockout expiry should be set"
    assert locked_user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS

    # Verify lockout duration (should be ~30 minutes)
    lockout_delta = (locked_user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
    print(f"  Lockout duration: {lockout_delta:.1f} minutes (expected: {LOCKOUT_DURATION_MINUTES})")
    assert 29 <= lockout_delta <= 31, f"Lockout duration should be ~{LOCKOUT_DURATION_MINUTES} minutes"

    print("[PASS] Test 1: Account locked after 5 failed attempts")
    return locked_user


async def test_locked_login_fails(db: AsyncSession):
    """Test: Locked account cannot login even with correct password"""
    print("\n=== Test 2: Locked Account Login ===")

    user = await auth_service.authenticate_user(db, "test_lockout", "correct_password")
    assert user is None, "Locked account should not authenticate"

    print("[PASS] Test 2: Locked account rejected correct password")


async def test_admin_unlock(db: AsyncSession, user_id):
    """Test: Admin can manually unlock account"""
    print("\n=== Test 3: Admin Manual Unlock ===")

    unlocked_user = await auth_service.unlock_account(db, user_id)

    assert unlocked_user is not None, "Unlock should succeed"
    assert unlocked_user.is_locked == False, "Account should be unlocked"
    assert unlocked_user.locked_until is None, "Lockout expiry should be cleared"
    assert unlocked_user.failed_login_attempts == 0, "Failed attempts should be reset"

    print(f"  User: {unlocked_user.username}")
    print(f"  is_locked: {unlocked_user.is_locked}")
    print(f"  failed_attempts: {unlocked_user.failed_login_attempts}")
    print("[PASS] Test 3: Admin successfully unlocked account")


async def test_unlocked_login_succeeds(db: AsyncSession):
    """Test: Unlocked account can login with correct password"""
    print("\n=== Test 4: Login After Unlock ===")

    user = await auth_service.authenticate_user(db, "test_lockout", "correct_password")

    assert user is not None, "Authentication should succeed"
    assert user.username == "test_lockout"
    assert user.failed_login_attempts == 0, "Failed attempts should be reset on success"
    assert user.last_login_at is not None, "Last login should be updated"

    print(f"  User: {user.username}")
    print(f"  last_login_at: {user.last_login_at}")
    print("[PASS] Test 4: Unlocked account can login successfully")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("FR-031 Account Lockout Feature Test")
    print("=" * 60)

    async with async_session() as db:
        try:
            # Setup
            await cleanup_test_user(db)
            test_user = await create_test_user(db)

            # Run tests
            await test_failed_logins(db)
            await test_locked_login_fails(db)
            await test_admin_unlock(db, test_user.id)
            await test_unlocked_login_succeeds(db)

            # Cleanup
            await cleanup_test_user(db)

            print("\n" + "=" * 60)
            print("ALL TESTS PASSED")
            print("=" * 60)

        except AssertionError as e:
            print(f"\nTEST FAILED")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            print(f"\nUNEXPECTED ERROR")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
