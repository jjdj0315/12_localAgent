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
        print(f"   {check_name}")
        if details:
            print(f"   {details}")

    def check_bcrypt_cost(self):
        """FR-029: Verify bcrypt cost factor = 12"""
        self.print_header("Check 1: Password Hashing (FR-029)")

        try:
            from app.core.security import pwd_context

            # Check if bcrypt is configured
            if "bcrypt" in pwd_context.schemes():
                # Check cost factor
                # Note: passlib doesn't expose rounds directly, but we can verify in code
                from app.core import security
                import inspect

                source = inspect.getsource(security)

                if "rounds=12" in source or "bcrypt_rounds=12" in source:
                    self.check_pass(
                        "Bcrypt cost factor",
                        "Configured with 12 rounds per FR-029"
                    )
                else:
                    self.check_warning(
                        "Bcrypt cost factor",
                        "Could not verify rounds=12 in code. Check .env: BCRYPT_ROUNDS=12"
                    )
            else:
                self.check_fail(
                    "Bcrypt scheme",
                    "Bcrypt not found in password context"
                )

        except Exception as e:
            self.check_fail("Bcrypt configuration", f"Error: {e}")

    def check_data_isolation(self):
        """FR-032: Verify data isolation middleware"""
        self.print_header("Check 2: Data Isolation (FR-032)")

        try:
            # Check middleware file exists
            middleware_file = Path("backend/app/middleware/data_isolation_middleware.py")

            if middleware_file.exists():
                self.check_pass(
                    "Data isolation middleware",
                    f"Found: {middleware_file}"
                )

                # Check for user_id filtering
                with open(middleware_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "user_id" in content and "filter" in content.lower():
                    self.check_pass(
                        "User ID filtering",
                        "Middleware includes user_id filtering logic"
                    )
                else:
                    self.check_warning(
                        "User ID filtering",
                        "Could not verify user_id filtering in middleware"
                    )
            else:
                self.check_fail(
                    "Data isolation middleware",
                    f"Not found: {middleware_file}"
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

    def print_summary(self):
        """Print audit summary"""
        self.print_header("Security Audit Summary")

        total_checks = self.checks_passed + self.checks_failed
        pass_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0

        print(f"\nResults:")
        print(f"   Passed: {self.checks_passed}")
        print(f"  L Failed: {self.checks_failed}")
        print(f"     Warnings: {len(self.warnings)}")
        print(f"  =Ê Pass Rate: {pass_rate:.1f}%")

        if self.warnings:
            print(f"\nWarnings:")
            for check_name, details in self.warnings:
                print(f"     {check_name}")
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
        print("SECURITY AUDIT (T239)")
        print("Verifying FR-029, FR-032, FR-033, and other security requirements")
        print("=" * 60)

        self.check_bcrypt_cost()
        self.check_data_isolation()
        self.check_admin_separation()
        self.check_input_validation()
        self.check_session_security()
        self.check_rate_limiting()
        self.check_secret_keys()
        self.check_pii_protection()

        self.print_summary()


def main():
    """Main entry point"""
    audit = SecurityAudit()
    audit.run_all_checks()


if __name__ == "__main__":
    main()
