#!/usr/bin/env python
"""Debug script to check database state"""

from database import UserDB
from datetime import datetime

# Create test parent
print("Creating parent account...")
success, parent_id = UserDB.create_user('debugparent@example.com', 'password123', 'Debug Parent', is_parent=True)
print(f"Success: {success}, ID: {parent_id}")

# Verify login
print("\nVerifying login...")
user = UserDB.verify_login('debugparent@example.com', 'password123')
print(f"User found: {user is not None}")
if user:
    print(f"  Email: {user.get('email')}")
    print(f"  Name: {user.get('name')}")
    print(f"  Account Type: {user.get('account_type')}")
    print(f"  ID: {user.get('_id')}")

# Try with existing user from test
print("\nVerifying test parent login...")
user = UserDB.verify_login('testparent@example.com', 'password123')
print(f"Test user found: {user is not None}")
if user:
    print(f"  Email: {user.get('email')}")
    print(f"  Name: {user.get('name')}")
    print(f"  Account Type: {user.get('account_type')}")
    print(f"  ID: {user.get('_id')}")
else:
    print("  Test user not found - may need to register again")
