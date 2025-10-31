"""
Python Dependencies Bundling Verification (T219)

Verifies that all Python dependencies can be installed offline from bundled wheels.
Tests FR-001: Air-gapped deployment requirement.

Usage:
    python backend/verify_python_dependencies.py

Setup:
    1. Download all wheels: pip download -r requirements.txt -d wheels/
    2. Run this script to verify offline installation
"""

import os
import sys
import subprocess
from pathlib import Path

print("=" * 60)
print("PYTHON DEPENDENCIES BUNDLING VERIFICATION (T219)")
print("=" * 60)

# Step 1: Check requirements.txt exists
print("\n[Step 1] Checking requirements.txt...")

requirements_file = Path("backend/requirements.txt")
if not requirements_file.exists():
    print(f"L ERROR: {requirements_file} not found")
    sys.exit(1)

print(f" Found: {requirements_file}")

# Read requirements
with open(requirements_file, 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"   Total packages: {len(requirements)}")

# Step 2: Check wheels directory
print("\n[Step 2] Checking wheels directory...")

wheels_dir = Path("backend/wheels")
if not wheels_dir.exists():
    print(f"L ERROR: {wheels_dir} not found")
    print("\n   Create wheels directory and download packages:")
    print(f"   mkdir {wheels_dir}")
    print(f"   pip download -r {requirements_file} -d {wheels_dir}")
    sys.exit(1)

print(f" Found: {wheels_dir}")

# List wheel files
wheel_files = list(wheels_dir.glob("*.whl"))
tar_files = list(wheels_dir.glob("*.tar.gz"))
all_packages = wheel_files + tar_files

print(f"   Wheel files: {len(wheel_files)}")
print(f"   Source tarballs: {len(tar_files)}")
print(f"   Total packages: {len(all_packages)}")

if len(all_packages) == 0:
    print(f"\nL ERROR: No package files found in {wheels_dir}")
    print("\n   Download packages with:")
    print(f"   pip download -r {requirements_file} -d {wheels_dir}")
    sys.exit(1)

# Step 3: Simulate offline installation (dry-run)
print("\n[Step 3] Simulating offline installation (dry-run)...")

try:
    # Use --dry-run to avoid actually installing
    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "--no-index",  # Do not use PyPI
            "--find-links", str(wheels_dir),  # Use local wheels
            "--dry-run",  # Don't actually install
            "-r", str(requirements_file)
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        print(" Offline installation simulation successful")
        print("\n   All dependencies can be installed from bundled wheels")
    else:
        print("L ERROR: Offline installation simulation failed")
        print("\nSTDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        sys.exit(1)

except subprocess.TimeoutExpired:
    print("L ERROR: Installation simulation timed out")
    sys.exit(1)
except Exception as e:
    print(f"L ERROR: {e}")
    sys.exit(1)

# Step 4: Check critical dependencies
print("\n[Step 4] Verifying critical dependencies...")

critical_packages = [
    "fastapi",
    "sqlalchemy",
    "alembic",
    "transformers",
    "torch",
    "sentence-transformers",
    "llama-cpp-python",
    "pydantic",
    "asyncpg",
    "python-multipart"
]

missing_critical = []

for package in critical_packages:
    # Check if package name appears in any wheel file
    found = any(
        package.lower().replace("-", "_") in file.name.lower() or
        package.lower().replace("_", "-") in file.name.lower()
        for file in all_packages
    )

    if found:
        print(f"    {package}")
    else:
        print(f"   L {package} (not found)")
        missing_critical.append(package)

if missing_critical:
    print(f"\nL ERROR: Missing critical packages: {missing_critical}")
    print("\n   These packages are required for air-gapped deployment.")
    print("   Download with:")
    print(f"   pip download {' '.join(missing_critical)} -d {wheels_dir}")
    sys.exit(1)

# Step 5: Calculate total size
print("\n[Step 5] Calculating bundle size...")

total_size = sum(f.stat().st_size for f in all_packages)
size_mb = total_size / 1024 / 1024
size_gb = size_mb / 1024

print(f"   Total size: {size_mb:.2f} MB ({size_gb:.2f} GB)")

if size_gb > 5:
    print(f"      WARNING: Bundle size exceeds 5GB")
    print(f"      Consider excluding development dependencies")

# Step 6: Generate installation instructions
print("\n[Step 6] Generating offline installation instructions...")

instructions_file = wheels_dir / "INSTALL.txt"
with open(instructions_file, 'w') as f:
    f.write("Offline Python Dependencies Installation\n")
    f.write("=" * 50 + "\n\n")
    f.write("Prerequisites:\n")
    f.write("  - Python 3.11+ installed\n")
    f.write("  - pip installed\n\n")
    f.write("Installation Steps:\n")
    f.write("  1. Navigate to project root\n\n")
    f.write("  2. Install from bundled wheels:\n")
    f.write(f"     pip install --no-index --find-links={wheels_dir} -r {requirements_file}\n\n")
    f.write("  3. Verify installation:\n")
    f.write("     python -c \"import fastapi; import transformers; print('Success')\"\n\n")
    f.write("Notes:\n")
    f.write("  - No internet connection required\n")
    f.write("  - All dependencies bundled in this directory\n")
    f.write(f"  - Total size: {size_mb:.2f} MB\n")

print(f" Created: {instructions_file}")

print("\n" + "=" * 60)
print("PYTHON DEPENDENCIES BUNDLING VERIFICATION: PASSED ")
print("=" * 60)
print("\nSummary:")
print(f"   Requirements file: {len(requirements)} packages")
print(f"   Bundled packages: {len(all_packages)} files")
print(f"   Critical dependencies: All present")
print(f"   Offline installation: Simulated successfully")
print(f"   Total size: {size_mb:.2f} MB")
print(f"   Installation instructions: Generated")
print("\nFR-001 (Air-gapped deployment) requirement satisfied.")
print("\nNext steps:")
print("  1. Transfer wheels/ directory to target system")
print(f"  2. Follow instructions in {instructions_file}")
