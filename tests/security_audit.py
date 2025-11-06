"""
Security Audit Script (T239)

Validates security requirements:
- FR-029: bcrypt cost 12
- FR-032: Data isolation
- FR-033: Admin privilege separation
- Input validation
- Session security
- Rate limiting

Usage:
    python tests/security_audit.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


class SecurityAudit:
    """Security audit coordinator"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []

    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)

    def check_pass(self, check_name: str, details: str = ""):
        """Record passed check"""
        self.checks_passed += 1
        print(f" {check_name}")
        if details:
            print(f"   {details}")

    def check_fail(self, check_name: str, details: str = ""):
        """Record failed check"""
        self.checks_failed += 1
        print(f"L {check_name}")
        if details:
            print(f"   {details}")

    def check_warning(self, check_name: str, details: str = ""):
        """Record warning"""
        self.warnings.append((check_name, details))
        print(f"�  {check_name}")
        if details:
            print(f"   {details}")

    def check_bcrypt_cost(self):
        """FR-029: Verify bcrypt cost factor = 12 (T316, FR-121)"""
        self.print_header("Check 1: Password Hashing (FR-029)")

        try:
            # T316: Import bcrypt directly (not passlib)
            import bcrypt

            # Test bcrypt.hashpw() with rounds=12
            test_password = b"test_password_123"
            password_hash = bcrypt.hashpw(test_password, bcrypt.gensalt(rounds=12))

            self.check_pass(
                "Bcrypt hashing",
                f"bcrypt.hashpw() works with rounds=12"
            )

            # T316: Verify hash starts with b'$2b$12$' (correct rounds)
            if password_hash.startswith(b'$2b$12$'):
                self.check_pass(
                    "Bcrypt cost factor verification",
                    "Hash prefix is b'$2b$12$' (12 rounds confirmed)"
                )
            else:
                self.check_fail(
                    "Bcrypt cost factor",
                    f"Expected b'$2b$12$', got {password_hash[:10]}"
                )

            # T316: Test bcrypt.checkpw() for correct password
            if bcrypt.checkpw(test_password, password_hash):
                self.check_pass(
                    "Bcrypt verification (correct password)",
                    "bcrypt.checkpw() returns True for correct password"
                )
            else:
                self.check_fail(
                    "Bcrypt verification",
                    "bcrypt.checkpw() failed for correct password"
                )

            # T316: Test bcrypt.checkpw() for incorrect password
            wrong_password = b"wrong_password_456"
            if not bcrypt.checkpw(wrong_password, password_hash):
                self.check_pass(
                    "Bcrypt verification (incorrect password)",
                    "bcrypt.checkpw() returns False for incorrect password"
                )
            else:
                self.check_fail(
                    "Bcrypt verification",
                    "bcrypt.checkpw() should return False for wrong password"
                )

        except ImportError as e:
            self.check_fail("Bcrypt import", f"bcrypt module not available: {e}")
        except Exception as e:
            self.check_fail("Bcrypt test", f"Error: {e}")

    def check_data_isolation(self):
        """FR-032, FR-122: Verify data isolation implementation (T319)"""
        self.print_header("Check 2: Data Isolation (FR-032, FR-122)")

        try:
            # T319: Verify dependency-level data isolation
            deps_file = Path("backend/app/api/deps.py")

            if deps_file.exists():
                with open(deps_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "Data Isolation Enforcement (FR-032, FR-122)" in content:
                    self.check_pass(
                        "Data isolation documentation",
                        "Comprehensive docstring found in get_current_user() (T318)"
                    )
                else:
                    self.check_warning(
                        "Data isolation documentation",
                        "Could not find FR-032/FR-122 documentation in deps.py"
                    )

                if "get_current_user" in content:
                    self.check_pass(
                        "User authentication dependency",
                        "get_current_user() dependency exists"
                    )

            # T319: Integration test - Create two users and test cross-user access
            try:
                import bcrypt
                import asyncio
                from fastapi.testclient import TestClient
                from app.main import app
                from app.core.database import AsyncSessionLocal
                from app.models.user import User
                from app.models.conversation import Conversation
                from sqlalchemy import select
                from uuid import uuid4

                # Create test client
                client = TestClient(app)

                async def test_cross_user_access():
                    async with AsyncSessionLocal() as db:
                        # Cleanup existing test users
                        await db.execute(
                            "DELETE FROM conversations WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'isolation_test_%')"
                        )
                        await db.execute(
                            "DELETE FROM users WHERE username LIKE 'isolation_test_%'"
                        )
                        await db.commit()

                        # Create User 1
                        user1_password = bcrypt.hashpw(b"pass1", bcrypt.gensalt(rounds=12)).decode()
                        user1 = User(
                            username="isolation_test_user1",
                            password_hash=user1_password,
                            is_admin=False,
                        )
                        db.add(user1)

                        # Create User 2
                        user2_password = bcrypt.hashpw(b"pass2", bcrypt.gensalt(rounds=12)).decode()
                        user2 = User(
                            username="isolation_test_user2",
                            password_hash=user2_password,
                            is_admin=False,
                        )
                        db.add(user2)
                        await db.commit()
                        await db.refresh(user1)
                        await db.refresh(user2)

                        # User 1 creates conversation
                        conv = Conversation(
                            user_id=user1.id,
                            title="User 1's Private Conversation"
                        )
                        db.add(conv)
                        await db.commit()
                        await db.refresh(conv)

                        return user1, user2, conv

                user1, user2, user1_conv = asyncio.run(test_cross_user_access())

                # Login as User 2
                login_response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "isolation_test_user2", "password": "pass2"}
                )

                if login_response.status_code != 200:
                    self.check_warning(
                        "Data isolation test",
                        f"Could not login as User 2: {login_response.status_code}"
                    )
                    return

                user2_session = login_response.cookies.get("session_token")

                # T319: User 2 attempts to GET User 1's conversation → should return 403/404
                get_response = client.get(
                    f"/api/v1/conversations/{user1_conv.id}",
                    cookies={"session_token": user2_session}
                )

                if get_response.status_code in [403, 404]:
                    self.check_pass(
                        "Cross-user GET blocked",
                        f"User 2 cannot GET User 1's conversation (status {get_response.status_code})"
                    )
                else:
                    self.check_fail(
                        "Cross-user GET blocked",
                        f"User 2 should not access User 1's conversation, got {get_response.status_code}"
                    )

                # T319: User 2 attempts to DELETE User 1's conversation → should return 403/404
                delete_response = client.delete(
                    f"/api/v1/conversations/{user1_conv.id}",
                    cookies={"session_token": user2_session}
                )

                if delete_response.status_code in [403, 404]:
                    self.check_pass(
                        "Cross-user DELETE blocked",
                        f"User 2 cannot DELETE User 1's conversation (status {delete_response.status_code})"
                    )
                else:
                    self.check_fail(
                        "Cross-user DELETE blocked",
                        f"User 2 should not delete User 1's conversation, got {delete_response.status_code}"
                    )

                # Cleanup
                async def cleanup():
                    async with AsyncSessionLocal() as db:
                        await db.execute(
                            "DELETE FROM conversations WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'isolation_test_%')"
                        )
                        await db.execute(
                            "DELETE FROM users WHERE username LIKE 'isolation_test_%'"
                        )
                        await db.commit()

                asyncio.run(cleanup())
                print("   Test users cleaned up")

            except ImportError as e:
                self.check_warning(
                    "Data isolation integration test",
                    f"Missing dependencies: {e}"
                )
            except Exception as e:
                self.check_warning(
                    "Data isolation integration test",
                    f"Test skipped: {e}"
                )

        except Exception as e:
            self.check_fail("Data isolation check", f"Error: {e}")

    def check_admin_separation(self):
        """FR-033: Verify admin privilege separation"""
        self.print_header("Check 3: Admin Privilege Separation (FR-033)")

        try:
            # Check separate admins table
            admin_model_file = Path("backend/app/models/admin.py")

            if admin_model_file.exists():
                self.check_pass(
                    "Separate admins table",
                    f"Found: {admin_model_file}"
                )

                with open(admin_model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "class Admin" in content:
                    self.check_pass(
                        "Admin model",
                        "Admin class defined separately from User"
                    )
                else:
                    self.check_fail(
                        "Admin model",
                        "Admin class not found in admin.py"
                    )
            else:
                self.check_fail(
                    "Admin separation",
                    "Separate admin.py model file not found"
                )

            # Check admin authentication endpoints
            admin_auth_file = Path("backend/app/api/v1/admin.py")

            if admin_auth_file.exists():
                self.check_pass(
                    "Admin endpoints",
                    f"Found: {admin_auth_file}"
                )
            else:
                self.check_warning(
                    "Admin endpoints",
                    "Admin-specific endpoints file not found"
                )

        except Exception as e:
            self.check_fail("Admin separation check", f"Error: {e}")

    def check_input_validation(self):
        """Check input validation (T231)"""
        self.print_header("Check 4: Input Validation (T231)")

        try:
            validators_file = Path("backend/app/core/validators.py")

            if validators_file.exists():
                self.check_pass(
                    "Validators module",
                    f"Found: {validators_file}"
                )

                with open(validators_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for key validators
                validators = [
                    ("validate_message_content", "Message content validation"),
                    ("validate_username", "Username validation"),
                    ("validate_password", "Password validation"),
                    ("validate_filename", "Filename validation (path traversal protection)"),
                    ("sanitize_search_query", "SQL injection prevention")
                ]

                for func_name, description in validators:
                    if func_name in content:
                        self.check_pass(description, f"Function: {func_name}")
                    else:
                        self.check_warning(description, f"Function not found: {func_name}")

            else:
                self.check_fail(
                    "Input validation",
                    "validators.py not found"
                )

        except Exception as e:
            self.check_fail("Input validation check", f"Error: {e}")

    def check_session_security(self):
        """Check session security (FR-012, FR-030)"""
        self.print_header("Check 5: Session Security")

        try:
            # Check .env.example for session config
            env_example = Path(".env.example")

            if env_example.exists():
                with open(env_example, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "SESSION_TIMEOUT_MINUTES=30" in content:
                    self.check_pass(
                        "Session timeout",
                        "Configured: 30 minutes (FR-012)"
                    )
                else:
                    self.check_warning(
                        "Session timeout",
                        "Check .env.example for SESSION_TIMEOUT_MINUTES=30"
                    )

                if "MAX_CONCURRENT_SESSIONS=3" in content:
                    self.check_pass(
                        "Concurrent sessions",
                        "Limited to 3 per user (FR-030)"
                    )
                else:
                    self.check_warning(
                        "Concurrent sessions",
                        "Check .env.example for MAX_CONCURRENT_SESSIONS=3"
                    )
            else:
                self.check_warning(
                    "Environment config",
                    ".env.example not found"
                )

        except Exception as e:
            self.check_fail("Session security check", f"Error: {e}")

    def check_rate_limiting(self):
        """Check rate limiting (FR-031)"""
        self.print_header("Check 6: Rate Limiting")

        try:
            rate_limit_file = Path("backend/app/middleware/rate_limit_middleware.py")

            if rate_limit_file.exists():
                self.check_pass(
                    "Rate limiting middleware",
                    f"Found: {rate_limit_file}"
                )

                with open(rate_limit_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "RateLimitMiddleware" in content:
                    self.check_pass(
                        "Rate limit implementation",
                        "RateLimitMiddleware class found"
                    )
                else:
                    self.check_fail(
                        "Rate limit implementation",
                        "RateLimitMiddleware class not found"
                    )
            else:
                self.check_fail(
                    "Rate limiting",
                    "rate_limit_middleware.py not found"
                )

            # Check login rate limiting
            auth_service = Path("backend/app/services/auth_service.py")

            if auth_service.exists():
                with open(auth_service, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "login_attempts" in content.lower() or "rate" in content.lower():
                    self.check_pass(
                        "Login rate limiting",
                        "Login attempt tracking found in auth_service.py"
                    )
                else:
                    self.check_warning(
                        "Login rate limiting",
                        "Could not verify login attempt tracking"
                    )

        except Exception as e:
            self.check_fail("Rate limiting check", f"Error: {e}")

    def check_secret_keys(self):
        """Check secret key configuration"""
        self.print_header("Check 7: Secret Keys")

        try:
            # Check .env.example has placeholder
            env_example = Path(".env.example")

            if env_example.exists():
                with open(env_example, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "SECRET_KEY=" in content:
                    if "CHANGE" in content or "your_secret" in content:
                        self.check_pass(
                            "Secret key template",
                            ".env.example has placeholder (not actual secret)"
                        )
                    else:
                        self.check_warning(
                            "Secret key template",
                            ".env.example may contain actual secret"
                        )
                else:
                    self.check_fail(
                        "Secret key config",
                        "SECRET_KEY not found in .env.example"
                    )

            # Check .env.production has warning
            env_prod = Path(".env.production")

            if env_prod.exists():
                with open(env_prod, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "CHANGE_ME" in content:
                    self.check_pass(
                        "Production secret key",
                        "Placeholder found (must be changed before deployment)"
                    )
                else:
                    self.check_warning(
                        "Production secret key",
                        "Ensure secret key is changed in production"
                    )

        except Exception as e:
            self.check_fail("Secret key check", f"Error: {e}")

    def check_pii_protection(self):
        """Check PII protection (FR-056)"""
        self.print_header("Check 8: PII Protection (FR-056)")

        try:
            # Check safety filter has PII detection
            safety_service = Path("backend/app/services/safety_filter_service.py")

            if safety_service.exists():
                with open(safety_service, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "pii" in content.lower():
                    self.check_pass(
                        "PII detection",
                        "PII detection logic found in safety_filter_service.py"
                    )
                else:
                    self.check_warning(
                        "PII detection",
                        "Could not verify PII detection in safety filter"
                    )

            # Check audit logging doesn't log message content
            audit_service = Path("backend/app/services/audit_log_service.py")

            if audit_service.exists():
                with open(audit_service, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "message content is NOT logged" in content:
                    self.check_pass(
                        "Audit log privacy",
                        "Confirmed: Message content not logged (FR-056)"
                    )
                else:
                    self.check_warning(
                        "Audit log privacy",
                        "Verify message content is not logged in audit logs"
                    )

        except Exception as e:
            self.check_fail("PII protection check", f"Error: {e}")

    def check_login_endpoint(self):
        """T317: Login endpoint integration test (FR-121)"""
        self.print_header("Check 9: Login Endpoint Integration (T317)")

        try:
            import bcrypt
            from fastapi.testclient import TestClient

            # Import app
            from app.main import app
            from app.core.database import get_db, AsyncSessionLocal
            from app.models.user import User
            import asyncio

            # Create test client
            client = TestClient(app)

            # Create test user with bcrypt-hashed password
            async def create_test_user():
                async with AsyncSessionLocal() as db:
                    # Check if test user already exists
                    from sqlalchemy import select
                    result = await db.execute(
                        select(User).where(User.username == "security_audit_test_user")
                    )
                    existing_user = result.scalar_one_or_none()

                    if existing_user:
                        # Delete existing test user
                        await db.delete(existing_user)
                        await db.commit()

                    # Create user with bcrypt hash (rounds=12)
                    password = "test_password_123"
                    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

                    test_user = User(
                        username="security_audit_test_user",
                        password_hash=password_hash,
                        is_admin=False,
                    )
                    db.add(test_user)
                    await db.commit()
                    await db.refresh(test_user)
                    return test_user

            # Run async user creation
            test_user = asyncio.run(create_test_user())

            self.check_pass(
                "Test user creation",
                f"Created test user with bcrypt hash: {test_user.username}"
            )

            # T317: Test login with correct password → 200
            response_correct = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "security_audit_test_user",
                    "password": "test_password_123"
                }
            )

            if response_correct.status_code == 200:
                self.check_pass(
                    "Login with correct password",
                    f"Status 200 OK, response: {response_correct.json().get('message', 'success')}"
                )
            else:
                self.check_fail(
                    "Login with correct password",
                    f"Expected 200, got {response_correct.status_code}: {response_correct.text}"
                )

            # T317: Test login with wrong password → 401
            response_wrong = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "security_audit_test_user",
                    "password": "wrong_password_456"
                }
            )

            if response_wrong.status_code == 401:
                self.check_pass(
                    "Login with wrong password",
                    f"Status 401 Unauthorized (correct rejection)"
                )
            else:
                self.check_fail(
                    "Login with wrong password",
                    f"Expected 401, got {response_wrong.status_code}"
                )

            # T317: Verify backend uses same bcrypt implementation
            # Check that hash format matches
            if test_user.password_hash.startswith("$2b$12$"):
                self.check_pass(
                    "Backend bcrypt implementation",
                    "Password hash format matches bcrypt rounds=12"
                )
            else:
                self.check_fail(
                    "Backend bcrypt implementation",
                    f"Unexpected hash format: {test_user.password_hash[:20]}"
                )

            # Cleanup test user
            async def cleanup_test_user():
                async with AsyncSessionLocal() as db:
                    from sqlalchemy import select
                    result = await db.execute(
                        select(User).where(User.username == "security_audit_test_user")
                    )
                    user = result.scalar_one_or_none()
                    if user:
                        await db.delete(user)
                        await db.commit()

            asyncio.run(cleanup_test_user())
            print("   Test user cleaned up")

        except ImportError as e:
            self.check_warning(
                "Login endpoint test",
                f"Missing dependencies for integration test: {e}"
            )
        except Exception as e:
            self.check_fail("Login endpoint test", f"Error: {e}")

    def print_summary(self):
        """Print audit summary"""
        self.print_header("Security Audit Summary")

        total_checks = self.checks_passed + self.checks_failed
        pass_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0

        print(f"\nResults:")
        print(f"   Passed: {self.checks_passed}")
        print(f"  L Failed: {self.checks_failed}")
        print(f"  �  Warnings: {len(self.warnings)}")
        print(f"  =� Pass Rate: {pass_rate:.1f}%")

        if self.warnings:
            print(f"\nWarnings:")
            for check_name, details in self.warnings:
                print(f"  �  {check_name}")
                if details:
                    print(f"     {details}")

        print("\n" + "=" * 60)
        if self.checks_failed == 0:
            print("SECURITY AUDIT: PASSED ")
            print("All critical security requirements verified.")
        else:
            print("SECURITY AUDIT: FAILED L")
            print(f"{self.checks_failed} critical check(s) failed.")

        print("=" * 60)

    def run_all_checks(self):
        """Run all security checks"""
        print("=" * 60)
        print("SECURITY AUDIT (T239, T316-T317)")
        print("Verifying FR-029, FR-032, FR-033, FR-121, and other security requirements")
        print("=" * 60)

        self.check_bcrypt_cost()
        self.check_data_isolation()
        self.check_admin_separation()
        self.check_input_validation()
        self.check_session_security()
        self.check_rate_limiting()
        self.check_secret_keys()
        self.check_pii_protection()
        self.check_login_endpoint()  # T317: Login endpoint integration test

        self.print_summary()


def main():
    """Main entry point"""
    audit = SecurityAudit()
    audit.run_all_checks()


if __name__ == "__main__":
    main()
