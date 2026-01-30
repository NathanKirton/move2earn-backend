"""
Database Management Script
Utilities for clearing databases, deleting accounts, and managing data

Run with caution - these operations are destructive!
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from database import get_db, UserDB
from bson import ObjectId

load_dotenv()

def get_mongo_connection():
    """Get MongoDB connection"""
    uri = os.getenv('MONGODB_URI')
    if not uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return None
    try:
        client = MongoClient(uri)
        return client
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        return None


def clear_all_users():
    """Delete all user accounts from the database"""
    response = input("WARNING: This will delete ALL user accounts. Type 'DELETE ALL' to confirm: ")
    if response != "DELETE ALL":
        print("Operation cancelled.")
        return
    
    client = get_mongo_connection()
    if client is None:
        print("ERROR: Could not connect to MongoDB")
        return
    
    try:
        # Connect to Move2EarnProject database
        db = client['Move2EarnProject']
        users_collection = db['users']
        result = users_collection.delete_many({})
        print(f"✓ Deleted {result.deleted_count} user accounts from Move2EarnProject")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        client.close()


def clear_all_activities():
    """Delete all activity records from the database"""
    response = input("WARNING: This will delete ALL activity records. Type 'DELETE ALL' to confirm: ")
    if response != "DELETE ALL":
        print("Operation cancelled.")
        return
    
    db = get_db()
    if db is None:
        print("ERROR: Could not connect to database")
        return
    
    try:
        activities_collection = db['activities']
        result = activities_collection.delete_many({})
        print(f"✓ Deleted {result.deleted_count} activity records")
    except Exception as e:
        print(f"ERROR: {e}")


def delete_user_by_email(email):
    """Delete a specific user account by email"""
    db = get_db()
    if db is None:
        print("ERROR: Could not connect to database")
        return
    
    try:
        users_collection = db['users']
        
        # Find user first
        user = users_collection.find_one({'email': email})
        if not user:
            print(f"User with email '{email}' not found")
            return
        
        # Delete the user
        result = users_collection.delete_one({'email': email})
        print(f"✓ Deleted user: {user.get('name')} ({email})")
        
        # If this was a child, remove from parent's children list
        if user.get('parent_id'):
            parent_id = user.get('parent_id')
            if isinstance(parent_id, str):
                parent_id = ObjectId(parent_id)
            users_collection.update_one(
                {'_id': parent_id},
                {'$pull': {'children': user['_id']}}
            )
            print(f"✓ Removed child from parent's account")
        
        # If this was a parent, optionally delete all children
        if user.get('children'):
            print(f"⚠ This parent has {len(user['children'])} child account(s)")
            del_children = input("Delete all child accounts too? (yes/no): ")
            if del_children.lower() == 'yes':
                users_collection.delete_many({'_id': {'$in': user['children']}})
                print(f"✓ Deleted {len(user['children'])} child account(s)")
    
    except Exception as e:
        print(f"ERROR: {e}")


def delete_user_by_id(user_id):
    """Delete a specific user account by ID"""
    db = get_db()
    if not db:
        print("ERROR: Could not connect to database")
        return
    
    try:
        users_collection = db['users']
        
        # Convert to ObjectId if string
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # Find user first
        user = users_collection.find_one({'_id': user_id})
        if not user:
            print(f"User with ID '{user_id}' not found")
            return
        
        # Delete the user
        result = users_collection.delete_one({'_id': user_id})
        print(f"✓ Deleted user: {user.get('name')} ({user.get('email')})")
        
        # If this was a child, remove from parent's children list
        if user.get('parent_id'):
            parent_id = user.get('parent_id')
            if isinstance(parent_id, str):
                parent_id = ObjectId(parent_id)
            users_collection.update_one(
                {'_id': parent_id},
                {'$pull': {'children': user_id}}
            )
            print(f"✓ Removed child from parent's account")
        
        # If this was a parent, optionally delete all children
        if user.get('children'):
            print(f"⚠ This parent has {len(user['children'])} child account(s)")
            del_children = input("Delete all child accounts too? (yes/no): ")
            if del_children.lower() == 'yes':
                users_collection.delete_many({'_id': {'$in': user['children']}})
                print(f"✓ Deleted {len(user['children'])} child account(s)")
    
    except Exception as e:
        print(f"ERROR: {e}")


def reset_user_game_time(email):
    """Reset game time for a specific user"""
    db = get_db()
    if db is None:
        print("ERROR: Could not connect to database")
        return
    
    try:
        users_collection = db['users']
        
        # Find user first
        user = users_collection.find_one({'email': email})
        if not user:
            print(f"User with email '{email}' not found")
            return
        
        # Reset game time
        users_collection.update_one(
            {'email': email},
            {'$set': {
                'earned_game_time': 0,
                'current_used_game_time': 0,
                'daily_screen_time_limit': 60
            }}
        )
        print(f"✓ Reset game time for {user.get('name')}")
        print(f"  - earned_game_time: 0")
        print(f"  - current_used_game_time: 0")
        print(f"  - daily_screen_time_limit: 60")
    
    except Exception as e:
        print(f"ERROR: {e}")


def reset_all_user_game_time():
    """Reset game time for all users"""
    response = input("WARNING: This will reset game time for ALL users. Type 'RESET ALL' to confirm: ")
    if response != "RESET ALL":
        print("Operation cancelled.")
        return
    
    db = get_db()
    if db is None:
        print("ERROR: Could not connect to database")
        return
    
    try:
        users_collection = db['users']
        
        result = users_collection.update_many(
            {},
            {'$set': {
                'earned_game_time': 0,
                'current_used_game_time': 0,
                'daily_screen_time_limit': 60,
                'streak_count': 0,
                'last_activity_date': None
            }}
        )
        print(f"✓ Reset game time for {result.modified_count} user(s)")
    
    except Exception as e:
        print(f"ERROR: {e}")


def list_all_users():
    """List all users in the database"""
    db = get_db()
    if db is None:
        print("ERROR: Could not connect to database")
        return
    
    try:
        users_collection = db['users']
        users = list(users_collection.find({}, {
            '_id': 1,
            'name': 1,
            'email': 1,
            'account_type': 1,
            'earned_game_time': 1,
            'current_used_game_time': 1,
            'daily_screen_time_limit': 1,
            'streak_count': 1
        }))
        
        if not users:
            print("No users found in database")
            return
        
        print(f"\n{'='*120}")
        print(f"{'Name':<20} {'Email':<30} {'Type':<15} {'Earned':<10} {'Used':<10} {'Limit':<10} {'Streak':<8}")
        print(f"{'='*120}")
        
        for user in users:
            name = user.get('name', 'Unknown')[:19]
            email = user.get('email', 'Unknown')[:29]
            account_type = user.get('account_type', 'Unknown')[:14]
            earned = str(user.get('earned_game_time', 0))[:9]
            used = str(user.get('current_used_game_time', 0))[:9]
            limit = str(user.get('daily_screen_time_limit', 0))[:9]
            streak = str(user.get('streak_count', 0))[:7]
            
            print(f"{name:<20} {email:<30} {account_type:<15} {earned:<10} {used:<10} {limit:<10} {streak:<8}")
        
        print(f"{'='*120}")
        print(f"Total users: {len(users)}")
    
    except Exception as e:
        print(f"ERROR: {e}")


def show_menu():
    """Display interactive menu"""
    while True:
        print("\n" + "="*50)
        print("Database Management Tool")
        print("="*50)
        print("1. List all users")
        print("2. Delete user by email")
        print("3. Delete user by ID")
        print("4. Reset game time for user")
        print("5. Reset all game time")
        print("6. Clear all activities")
        print("7. Clear all users")
        print("8. Exit")
        print("="*50)
        
        choice = input("Enter your choice (1-8): ").strip()
        
        if choice == '1':
            list_all_users()
        elif choice == '2':
            email = input("Enter user email: ").strip()
            if email:
                delete_user_by_email(email)
        elif choice == '3':
            user_id = input("Enter user ID (MongoDB ObjectId): ").strip()
            if user_id:
                delete_user_by_id(user_id)
        elif choice == '4':
            email = input("Enter user email: ").strip()
            if email:
                reset_user_game_time(email)
        elif choice == '5':
            reset_all_user_game_time()
        elif choice == '6':
            clear_all_activities()
        elif choice == '7':
            clear_all_users()
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    print("\n⚠️  WARNING: Database Management Tool ⚠️")
    print("This tool can permanently delete or modify data.")
    print("Use with extreme caution!\n")
    
    show_menu()
