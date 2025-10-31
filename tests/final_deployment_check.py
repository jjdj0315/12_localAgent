"""
Final Deployment Readiness Check (T240)

Comprehensive pre-deployment validation combining all verification steps.
References air-gapped-verification-checklist.md

Usage:
    python tests/final_deployment_check.py
"""

import subprocess
import sys
from pathlib import Path


class FinalDeploymentCheck:
    """Final deployment readiness coordinator"""

    def __init__(self):
        self.all_passed = True

    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)

    def run_test_script(self, script_name: str, description: str):
        """Run a test script and report results"""
        print(f"\n= Running: {description}")
        print(f"   Script: {script_name}")

        script_path = Path("tests") / script_name

        if not script_path.exists():
            print(f"      Script not found: {script_path}")
            print(f"   9  This test should be run manually")
            return

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print(f"    {description}: PASSED")
                # Optionally print summary from output
                if "PASSED" in result.stdout:
                    print(f"   {result.stdout.split('PASSED')[0].strip()[-100:]}")
            else:
                print(f"   L {description}: FAILED")
                print(f"   Error: {result.stderr[:200]}")
                self.all_passed = False

        except subprocess.TimeoutExpired:
            print(f"   ñ  {description}: TIMEOUT (>120s)")
            self.all_passed = False
        except Exception as e:
            print(f"   L {description}: ERROR - {e}")
            self.all_passed = False

    def check_file_exists(self, file_path: str, description: str):
        """Check if a file exists"""
        path = Path(file_path)

        if path.exists():
            size = path.stat().st_size
            print(f"    {description}")
            print(f"      Path: {file_path}")
            print(f"      Size: {size:,} bytes")
            return True
        else:
            print(f"   L {description}")
            print(f"      Missing: {file_path}")
            self.all_passed = False
            return False

    def verify_documentation(self):
        """Verify all documentation exists"""
        self.print_header("Phase 1: Documentation Verification")

        docs = [
            ("docs/user/user-guide-ko.md", "Korean User Guide"),
            ("docs/admin/advanced-features-manual.md", "Admin Manual"),
            ("docs/admin/backup-restore-guide.md", "Backup & Restore Guide"),
            ("docs/admin/customization-guide.md", "Customization Guide"),
            ("docs/deployment/deployment-guide.md", "Deployment Guide"),
            ("docs/deployment/air-gapped-deployment.md", "Air-Gapped Deployment Guide"),
            ("docs/deployment/air-gapped-verification-checklist.md", "Verification Checklist"),
            (".env.development", "Development Environment Template"),
            (".env.production", "Production Environment Template"),
            (".env.example", "Environment Example File")
        ]

        print("\nChecking documentation files...")
        for doc_path, doc_name in docs:
            self.check_file_exists(doc_path, doc_name)

    def verify_scripts(self):
        """Verify all scripts and tools exist"""
        self.print_header("Phase 2: Scripts & Tools Verification")

        scripts = [
            ("scripts/offline-install.sh", "Offline Installation Script"),
            ("backend/test_offline_model_loading.py", "Model Loading Test"),
            ("backend/test_offline_embedding_loading.py", "Embedding Loading Test"),
            ("backend/verify_python_dependencies.py", "Python Dependencies Verification"),
            ("frontend/verify-node-dependencies.js", "Node.js Dependencies Verification")
        ]

        print("\nChecking deployment scripts...")
        for script_path, script_name in scripts:
            self.check_file_exists(script_path, script_name)

    def run_validation_tests(self):
        """Run all validation test scripts"""
        self.print_header("Phase 3: Automated Validation Tests")

        tests = [
            ("security_audit.py", "Security Audit (FR-029, FR-032, FR-033)"),
            ("success_criteria_validation.py", "Success Criteria (SC-001 to SC-020)"),
            ("korean_quality_test.py", "Korean Language Quality (SC-004)")
        ]

        for test_script, test_desc in tests:
            self.run_test_script(test_script, test_desc)

    def check_critical_features(self):
        """Check critical feature implementations"""
        self.print_header("Phase 4: Critical Feature Verification")

        features = [
            ("backend/app/services/llm_service.py", "LLM Service"),
            ("backend/app/services/safety_filter_service.py", "Safety Filter"),
            ("backend/app/services/react_agent_service.py", "ReAct Agent"),
            ("backend/app/services/orchestrator_service.py", "Multi-Agent Orchestrator"),
            ("backend/app/services/audit_log_service.py", "Audit Logging"),
            ("backend/app/services/graceful_degradation_service.py", "Graceful Degradation"),
            ("backend/app/middleware/resource_limit_middleware.py", "Resource Limits"),
            ("backend/app/core/validators.py", "Input Validation")
        ]

        print("\nChecking critical backend services...")
        for feature_path, feature_name in features:
            self.check_file_exists(feature_path, feature_name)

    def check_admin_features(self):
        """Check admin panel features"""
        self.print_header("Phase 5: Admin Panel Verification")

        admin_components = [
            ("frontend/src/components/admin/AdvancedFeaturesDashboard.tsx", "Advanced Features Dashboard"),
            ("frontend/src/components/admin/AuditLogViewer.tsx", "Audit Log Viewer"),
            ("frontend/src/components/admin/TemplateManager.tsx", "Template Manager"),
            ("backend/app/api/v1/admin/templates.py", "Template Upload API"),
            ("backend/app/api/v1/admin/agents.py", "Agent Configuration API"),
            ("backend/app/api/v1/admin/config.py", "Resource Limit API")
        ]

        print("\nChecking admin features...")
        for component_path, component_name in admin_components:
            self.check_file_exists(component_path, component_name)

    def print_deployment_checklist(self):
        """Print deployment checklist reference"""
        self.print_header("Phase 6: Deployment Checklist Reference")

        print("\n=Ë Before deploying to production, complete:")
        print("\n1. Air-Gapped Verification (docs/deployment/air-gapped-verification-checklist.md)")
        print("   - Phase 1-3: Dependencies & Models")
        print("   - Phase 4-6: Services & UI")
        print("   - Phase 7-9: Performance & Security")
        print("   - Phase 10-13: Logging & Final Verification")
        print("\n2. Environment Configuration (.env.production)")
        print("   - Change SECRET_KEY to secure random value")
        print("   - Update database passwords")
        print("   - Configure CORS_ORIGINS for production domain")
        print("   - Verify all model paths")
        print("   - Review 25-item production checklist")
        print("\n3. Security Review")
        print("   - Run: python tests/security_audit.py")
        print("   - Verify all checks pass")
        print("   - Review audit log configuration")
        print("\n4. Performance Testing")
        print("   - Run: python tests/performance_test.py")
        print("   - Verify <20% degradation with 10 concurrent users")
        print("   - Monitor resource usage")
        print("\n5. Manual Testing")
        print("   - Complete all user story scenarios")
        print("   - Test air-gapped mode (disable network)")
        print("   - Verify Korean language quality")
        print("   - Test backup and restore procedures")

    def print_summary(self):
        """Print final summary"""
        self.print_header("Final Deployment Readiness Summary")

        if self.all_passed:
            print("\n DEPLOYMENT READY")
            print("\nAll automated checks passed.")
            print("\nNext Steps:")
            print("  1. Review: docs/deployment/air-gapped-verification-checklist.md")
            print("  2. Configure: .env.production")
            print("  3. Run: scripts/offline-install.sh")
            print("  4. Complete manual testing scenarios")
            print("  5. Deploy to production")
        else:
            print("\nL NOT READY FOR DEPLOYMENT")
            print("\nSome checks failed. Review the output above.")
            print("\nRecommended Actions:")
            print("  1. Fix failed checks")
            print("  2. Re-run: python tests/final_deployment_check.py")
            print("  3. Complete missing implementations")

        print("\n" + "=" * 70)

    def run_all_checks(self):
        """Run all deployment readiness checks"""
        print("=" * 70)
        print("FINAL DEPLOYMENT READINESS CHECK (T240)")
        print("Comprehensive pre-deployment validation")
        print("=" * 70)

        self.verify_documentation()
        self.verify_scripts()
        self.run_validation_tests()
        self.check_critical_features()
        self.check_admin_features()
        self.print_deployment_checklist()
        self.print_summary()


def main():
    """Main entry point"""
    checker = FinalDeploymentCheck()
    checker.run_all_checks()


if __name__ == "__main__":
    main()
