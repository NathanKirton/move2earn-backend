#!/usr/bin/env python
"""Diagnose user accounts and password hashing"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from database import hash_password, verify_password
import bcrypt

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')

try:
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000
    )
    client.admin.command('ping')
    db = client[MONGODB_DB_NAME]
    users_collection = db['users']
    
    print("=" * 60)
    print("USERS IN DATABASE")
    print("=" * 60)
    
    all_users = users_collection.find()
    for user in all_users:
        print(f"\nEmail: {user['email']}")
        print(f"Name: {user.get('name', 'N/A')}")
        print(f"Password Hash: {user['password'][:40]}...")
        print(f"Strava Connected: {user.get('strava_connected', False)}")
    
    # Test password hashing/verification
    print("\n" + "=" * 60)
    print("PASSWORD HASHING TEST")
    print("=" * 60)
    
    test_password = "TestPassword123"
    print(f"\nTest password: {test_password}")
    
    hashed = hash_password(test_password)
    print(f"Hashed: {hashed[:40]}...")
    
    verified = verify_password(test_password, hashed)
    print(f"Verification result: {verified}")
    
    # Try with wrong password
    wrong_verified = verify_password("WrongPassword123", hashed)
    print(f"Wrong password verification: {wrong_verified}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
