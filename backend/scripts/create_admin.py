#!/usr/bin/env python3
"""Script to create an admin user"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SyncSessionLocal
from app.core.security import hash_password
from app.models.user import User


def create_admin(username: str, password: str) -> None:
    """
    Create an admin user.

    Args:
        username: Admin username
        password: Admin password
    """
    db = SyncSessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"Error: User '{username}' already exists!")
            return

        # Create admin user
        hashed_password = hash_password(password)
        admin_user = User(
            username=username, password_hash=hashed_password, is_admin=True
        )

        db.add(admin_user)
        db.commit()

        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Username: {username}")
        print(f"   Is Admin: True")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")

    args = parser.parse_args()

    # Validate password
    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters long!")
        sys.exit(1)

    create_admin(args.username, args.password)


if __name__ == "__main__":
    main()
