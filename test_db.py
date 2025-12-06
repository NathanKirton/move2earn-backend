#!/usr/bin/env python
"""Test MongoDB connection"""
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')

print(f"MongoDB URI: {MONGODB_URI}")
print(f"Database Name: {MONGODB_DB_NAME}")
print()

print("Attempting to connect to MongoDB...")
print("Note: This may take a minute due to DNS lookups...")

try:
    from pymongo import MongoClient
    
    # Try with longer timeouts
    print("Connecting with 30-second timeout...")
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        retryWrites=True
    )
    
    print("Pinging MongoDB...")
    client.admin.command('ping')
    print("✓ MongoDB connection successful!")
    
    db = client[MONGODB_DB_NAME]
    print(f"✓ Connected to database: {MONGODB_DB_NAME}")
    print(f"✓ Database collections: {db.list_collection_names()}")
    
except Exception as e:
    print(f"✗ Connection failed: {type(e).__name__}: {e}")
    print()
    print("Troubleshooting tips:")
    print("1. Check your MongoDB Atlas credentials")
    print("2. Verify your IP address is whitelisted in MongoDB Atlas")
    print("3. Check your network firewall settings")
    print("4. Try using a different DNS server (e.g., 8.8.8.8)")
