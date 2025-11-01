"""
Initial Setup Service

Handles first-run setup wizard and setup.lock file mechanism per FR-034.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.admin import Admin
from ..models.user import User
from ..core.security import get_password_hash


# Setup lock file path (project root)
SETUP_LOCK_PATH = Path(__file__).parent.parent.parent.parent / "setup.lock"


class SetupService:
    """Service for managing initial system setup."""

    @staticmethod
    def is_setup_complete() -> bool:
        """
        Check if initial setup has been completed.

        Returns:
            bool: True if setup.lock file exists, False otherwise
        """
        return SETUP_LOCK_PATH.exists()

    @staticmethod
    def create_initial_admin(
        username: str,
        password: str,
        system_name: Optional[str] = None,
        storage_path: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, str]:
        """
        Create the first administrator account and complete setup.

        Args:
            username: Administrator username
            password: Administrator password (plain text, will be hashed)
            system_name: Optional system name configuration
            storage_path: Optional storage path configuration
            db: Database session

        Returns:
            Dict with success message and admin details

        Raises:
            ValueError: If setup is already complete
            ValueError: If admin creation fails
        """
        # Check if setup already complete
        if SetupService.is_setup_complete():
            raise ValueError("Setup has already been completed. setup.lock file exists.")

        # Use provided session or create new one
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            # Check if any admin already exists in database
            existing_admin = db.query(Admin).first()
            if existing_admin:
                raise ValueError("Administrator already exists in database.")

            # Create user account
            user = User(
                username=username,
                hashed_password=get_password_hash(password),
                is_active=True
            )
            db.add(user)
            db.flush()  # Get user.id

            # Create admin entry
            admin = Admin(
                user_id=user.id,
                can_manage_users=True,
                can_view_logs=True,
                can_modify_settings=True
            )
            db.add(admin)
            db.commit()

            # Create setup.lock file
            SetupService._create_lock_file(system_name, storage_path)

            return {
                "message": "Initial setup completed successfully",
                "admin_username": username,
                "admin_id": str(admin.id),
                "user_id": str(user.id)
            }

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create initial administrator: {str(e)}")

        finally:
            if close_session:
                db.close()

    @staticmethod
    def _create_lock_file(system_name: Optional[str] = None, storage_path: Optional[str] = None):
        """
        Create setup.lock file in project root.

        Args:
            system_name: Optional system name to store in lock file
            storage_path: Optional storage path to store in lock file
        """
        try:
            # Ensure parent directory exists
            SETUP_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Write lock file with metadata
            with open(SETUP_LOCK_PATH, 'w', encoding='utf-8') as f:
                f.write("# Setup Completed\n")
                f.write("# This file prevents the setup wizard from running again.\n")
                f.write("# DO NOT DELETE unless you want to reinitialize the system.\n\n")

                if system_name:
                    f.write(f"SYSTEM_NAME={system_name}\n")
                if storage_path:
                    f.write(f"STORAGE_PATH={storage_path}\n")

            print(f"✓ Setup lock file created: {SETUP_LOCK_PATH}")

        except Exception as e:
            raise ValueError(f"Failed to create setup.lock file: {str(e)}")

    @staticmethod
    def get_setup_info() -> Optional[Dict[str, str]]:
        """
        Read setup information from lock file.

        Returns:
            Dict with setup info if lock file exists, None otherwise
        """
        if not SETUP_LOCK_PATH.exists():
            return None

        info = {"lock_file_path": str(SETUP_LOCK_PATH)}

        try:
            with open(SETUP_LOCK_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            info[key.lower()] = value
        except Exception as e:
            print(f"Warning: Could not read setup.lock file: {e}")

        return info
