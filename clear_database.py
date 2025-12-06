#!/usr/bin/env python
"""Clear all accounts from the database"""
import os
from dotenv import load_dotenv
from database import get_db

load_dotenv()

try:
    db = get_db()
    if db is None:
        print("✗ Failed to connect to database")
        exit(1)
    
    # Delete all users
    users_collection = db['users']
    result = users_collection.delete_many({})
    
    print(f"✓ Deleted {result.deleted_count} user accounts")
    
    # Delete all activities
    activities_collection = db['activities']
    result = activities_collection.delete_many({})
    
    print(f"✓ Deleted {result.deleted_count} activities")
    
    print("\n✓ Database cleared successfully")
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
