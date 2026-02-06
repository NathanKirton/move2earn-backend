#!/usr/bin/env python
"""
Quick database cleanup script
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def clean_database():
    """Clean all data from MongoDB"""
    uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('MONGODB_DB_NAME', 'move2earn')
    
    if not uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return
    
    try:
        client = MongoClient(uri)
        db = client[db_name]
        
        # Get all collections and delete them
        collections = db.list_collection_names()
        print(f"Found {len(collections)} collections to clean...")
        
        for collection_name in collections:
            collection = db[collection_name]
            result = collection.delete_many({})
            print(f"✓ Cleared '{collection_name}': {result.deleted_count} documents deleted")
        
        print("\n✓ Database cleaned successfully!")
        client.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    clean_database()
