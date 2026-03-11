#!/usr/bin/env python3
"""
Script to clear all accounts and activities from MongoDB database.
Use with caution - this is destructive!
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'move2earn')

def clear_database():
    """Delete all documents from users and activities collections"""
    
    if not MONGODB_URI:
        print("ERROR: MONGODB_URI environment variable is not set")
        return False
    
    try:
        print(f"Connecting to MongoDB database: {MONGODB_DB_NAME}")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        
        # Verify connection
        client.admin.command('ping')
        print("✓ Connected to MongoDB")
        
        db = client[MONGODB_DB_NAME]
        
        # Clear collections
        print("\nClearing collections...")
        
        # Clear users collection
        users_result = db['users'].delete_many({})
        print(f"✓ Deleted {users_result.deleted_count} user documents")
        
        # Clear activities collection
        activities_result = db['activities'].delete_many({})
        print(f"✓ Deleted {activities_result.deleted_count} activity documents")
        
        # Clear user_profiles collection (if exists)
        try:
            profiles_result = db['user_profiles'].delete_many({})
            print(f"✓ Deleted {profiles_result.deleted_count} user profile documents")
        except:
            pass
        
        # Clear challenges collection (if exists)
        try:
            challenges_result = db['challenges'].delete_many({})
            print(f"✓ Deleted {challenges_result.deleted_count} challenge documents")
        except:
            pass
        
        # Clear user_challenges collection (if exists)
        try:
            user_challenges_result = db['user_challenges'].delete_many({})
            print(f"✓ Deleted {user_challenges_result.deleted_count} user challenge documents")
        except:
            pass
        
        print("\n✓ Database cleared successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == '__main__':
    import sys
    
    # Confirmation prompt
    print("=" * 60)
    print("WARNING: This will DELETE ALL accounts and activities!")
    print("=" * 60)
    response = input("\nAre you sure? Type 'yes' to confirm: ")
    
    if response.lower() == 'yes':
        clear_database()
    else:
        print("Cancelled.")
        sys.exit(1)
