#!/usr/bin/env python3
"""
Reset game times for all child accounts.
Sets: used_game_time = 0, last_daily_reset = today (UTC), timer_running = False, timer_started_at = None
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')

if not MONGODB_URI or not MONGODB_DB_NAME:
    print("Error: MONGODB_URI and MONGODB_DB_NAME must be set in .env")
    exit(1)

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[MONGODB_DB_NAME]
    users = db['users']
    
    today = datetime.utcnow().date().isoformat()
    
    # Update all child accounts (where account_type is 'child')
    result = users.update_many(
        {'account_type': 'child'},
        {
            '$set': {
                'used_game_time': 0,
                'last_daily_reset': today,
                'timer_running': False,
                'timer_started_at': None
            }
        }
    )
    
    print(f"✓ Reset complete!")
    print(f"  Matched: {result.matched_count} child accounts")
    print(f"  Modified: {result.modified_count} accounts")
    print(f"  - used_game_time set to 0")
    print(f"  - last_daily_reset set to {today}")
    print(f"  - timer_running set to False")
    print(f"  - timer_started_at set to None")
    
    client.close()
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)
