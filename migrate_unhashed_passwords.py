#!/usr/bin/env python3
"""
Migration script to convert all user passwords to plaintext per request.
Rule: set password to the current username for every user (including superadmin),
unless a plaintext is already present (cannot detect reliably), we will overwrite.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User


def migrate_unhashed_passwords():
    with app.app_context():
        users = User.query.all()
        for u in users:
            u.password_hash = u.username
        db.session.commit()
        print(f"Updated {len(users)} users: password set to their username (plaintext).")
    return True


if __name__ == "__main__":
    ok = migrate_unhashed_passwords()
    sys.exit(0 if ok else 1)


