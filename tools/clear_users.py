#!/usr/bin/env python
"""Clear test users from database"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

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
    
    print("Current users:")
    all_users = users_collection.find()
    count = 0
    for user in all_users:
        count += 1
        print(f"  - {user['email']} (name: {user.get('name', 'N/A')})")
    
    if count > 0:
        confirm = input(f"\nDelete all {count} users? (yes/no): ")
        if confirm.lower() == 'yes':
            result = users_collection.delete_many({})
            print(f"Deleted {result.deleted_count} users")
        else:
            print("Cancelled")
    else:
        print("No users to delete")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
