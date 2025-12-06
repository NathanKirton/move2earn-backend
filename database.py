from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')

# Initialize MongoDB client lazily to avoid blocking on startup
client = None
db = None


def get_db():
    """Get MongoDB database connection, creating it if needed"""
    global client, db
    
    if db is not None:
        return db
    
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            retryWrites=True
        )
        # Verify connection
        client.admin.command('ping')
        db = client[MONGODB_DB_NAME]
        print("✓ Connected to MongoDB")
        return db
    except ConnectionFailure as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return None
    except Exception as e:
        print(f"✗ MongoDB Connection Error: {e}")
        return None


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class UserDB:
    """User database operations"""
    
    @staticmethod
    def create_user(email, password, name, is_parent=False):
        """Create a new user"""
        database = get_db()
        if database is None:
            return False, "Database connection failed"
        
        users = database['users']
        
        # Check if user already exists
        if users.find_one({'email': email}):
            return False, "Email already registered"
        
        # Hash password
        hashed_password = hash_password(password)
        print(f"DEBUG: Creating user {email} with password length {len(password)}")
        print(f"DEBUG: Hashed password: {hashed_password[:20]}...")
        
        # Create user document
        user_doc = {
            'email': email,
            'password': hashed_password,
            'name': name,
            'created_at': datetime.utcnow(),
            'account_type': 'parent' if is_parent else 'child',
            'strava_connected': False,
            'strava_id': None,
            'strava_access_token': None,
            'strava_refresh_token': None,
            'strava_token_expiry': None
        }
        
        # Parent-specific fields
        if is_parent:
            user_doc['children'] = []
        # Child-specific fields
        else:
            user_doc['parent_id'] = None
            user_doc['daily_screen_time_limit'] = 60  # Default 60 minutes
            user_doc['weekly_screen_time_limit'] = 420  # Default 7 hours
            user_doc['earned_game_time'] = 0  # Earned minutes
            user_doc['used_game_time'] = 0  # Used minutes
            user_doc['parent_messages'] = []  # Messages from parent
        
        try:
            result = users.insert_one(user_doc)
            return True, str(result.inserted_id)
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        database = get_db()
        if database is None:
            return None
        
        users = database['users']
        return users.find_one({'email': email})
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        database = get_db()
        if database is None:
            return None
        
        from bson import ObjectId
        users = database['users']
        
        try:
            return users.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    
    @staticmethod
    def verify_login(email, password):
        """Verify user email and password"""
        user = UserDB.get_user_by_email(email)
        
        if user is None:
            print(f"DEBUG: User not found for email: {email}")
            return None
        
        print(f"DEBUG: User found: {email}")
        print(f"DEBUG: Password input length: {len(password)}")
        print(f"DEBUG: Hashed password in DB: {user['password'][:20]}...")
        
        if verify_password(password, user['password']):
            print(f"DEBUG: Password verification PASSED")
            return user
        
        print(f"DEBUG: Password verification FAILED")
        return None
    
    @staticmethod
    def update_strava_credentials(user_id, athlete_id=None, athlete_name=None, access_token=None, refresh_token=None, token_expiry=None):
        """Update user's Strava credentials"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'strava_id': athlete_id,
                    'strava_access_token': access_token,
                    'strava_refresh_token': refresh_token,
                    'strava_token_expiry': token_expiry,
                    'strava_connected': True,
                    'strava_athlete_name': athlete_name
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating Strava credentials: {e}")
            return False
    
    @staticmethod
    def get_strava_token(user_id):
        """Get user's Strava access token"""
        user = UserDB.get_user_by_id(user_id)
        if user:
            return user.get('strava_access_token')
        return None
    
    @staticmethod
    def update_strava_token(user_id, access_token, refresh_token, expires_at):
        """Update Strava token for user"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'strava_access_token': access_token,
                    'strava_refresh_token': refresh_token,
                    'strava_token_expiry': expires_at
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating Strava token: {e}")
            return False

    @staticmethod
    def set_timer_state(child_id, running, started_at=None):
        """Set the child's timer running state and optionally the start timestamp."""
        database = get_db()
        if database is None:
            return False

        from bson import ObjectId
        users = database['users']

        update_data = {'timer_running': bool(running)}
        if started_at is not None:
            update_data['timer_started_at'] = started_at
        else:
            update_data['timer_started_at'] = None

        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error setting timer state: {e}")
            return False

    @staticmethod
    def get_timer_info(child_id):
        """Return timer info for a child (timer_running and timer_started_at)"""
        child = UserDB.get_user_by_id(child_id)
        if not child:
            return {'timer_running': False, 'timer_started_at': None}

        return {
            'timer_running': child.get('timer_running', False),
            'timer_started_at': child.get('timer_started_at')
        }

    @staticmethod
    def add_child(parent_id, child_email, child_password, child_name):
        """Add a child to parent's account"""
        database = get_db()
        if database is None:
            return False, "Database connection failed"
        
        from bson import ObjectId
        users = database['users']
        
        # Create child user first
        success, child_id = UserDB.create_user(child_email, child_password, child_name, is_parent=False)
        if not success:
            return False, f"Failed to create child account: {child_id}"
        
        try:
            # Add child to parent's children list
            users.update_one(
                {'_id': ObjectId(parent_id)},
                {'$push': {'children': ObjectId(child_id)}}
            )
            
            # Set parent_id on child
            users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': {'parent_id': ObjectId(parent_id)}}
            )
            
            return True, str(child_id)
        except Exception as e:
            print(f"Error adding child: {e}")
            return False, str(e)

    @staticmethod
    def get_parent_children(parent_id):
        """Get all children for a parent"""
        database = get_db()
        if database is None:
            return []
        
        from bson import ObjectId
        parent = UserDB.get_user_by_id(parent_id)
        if not parent or parent.get('account_type') != 'parent':
            return []
        
        users = database['users']
        children_ids = parent.get('children', [])
        children = []
        
        for child_id in children_ids:
            child = users.find_one({'_id': child_id})
            if child:
                children.append({
                    'id': str(child['_id']),
                    'name': child['name'],
                    'email': child['email'],
                    'earned_game_time': child.get('earned_game_time', 0),
                    'used_game_time': child.get('used_game_time', 0),
                    'daily_screen_time_limit': child.get('daily_screen_time_limit', 60),
                    'weekly_screen_time_limit': child.get('weekly_screen_time_limit', 420),
                    'timer_running': child.get('timer_running', False),
                    'timer_started_at': child.get('timer_started_at')
                })
        
        return children

    @staticmethod
    def update_child_screen_time_limit(child_id, daily_limit=None, weekly_limit=None):
        """Update screen time limits for a child"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        update_data = {}
        if daily_limit is not None:
            update_data['daily_screen_time_limit'] = daily_limit
        if weekly_limit is not None:
            update_data['weekly_screen_time_limit'] = weekly_limit
        
        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating screen time limits: {e}")
            return False

    @staticmethod
    def add_earned_game_time(child_id, minutes):
        """Add earned game time to child's account"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$inc': {'earned_game_time': minutes}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding earned game time: {e}")
            return False

    @staticmethod
    def add_earned_game_time_and_increase_limit(child_id, minutes):
        """Add earned game time and also increase the child's daily screen time limit by the same amount."""
        database = get_db()
        if database is None:
            return False

        from bson import ObjectId
        users = database['users']

        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$inc': {'earned_game_time': minutes, 'daily_screen_time_limit': minutes}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding earned game time and increasing limit: {e}")
            return False

    @staticmethod
    def use_game_time(child_id, minutes):
        """Deduct game time from child's available time"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$inc': {'used_game_time': minutes}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error using game time: {e}")
            return False

    @staticmethod
    def get_child_game_time_balance(child_id):
        """Get remaining game time balance for a child"""
        child = UserDB.get_user_by_id(child_id)
        if not child:
            return 0
        
        earned = child.get('earned_game_time', 0)
        used = child.get('used_game_time', 0)
        return max(0, earned - used)

    @staticmethod
    def add_parent_message(child_id, parent_name, message, minutes=0):
        """Add a message from parent to child (with optional bonus time)"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            message_doc = {
                'from_parent': parent_name,
                'message': message,
                'bonus_minutes': minutes,
                'created_at': datetime.utcnow(),
                'read': False
            }
            
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$push': {'parent_messages': message_doc}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding parent message: {e}")
            return False

    @staticmethod
    def get_parent_messages(child_id):
        """Get all messages from parent for a child"""
        child = UserDB.get_user_by_id(child_id)
        if not child:
            return []
        
        messages = child.get('parent_messages', [])
        # Sort by most recent first
        return sorted(messages, key=lambda x: x.get('created_at', datetime.utcnow()), reverse=True)

    @staticmethod
    def mark_message_as_read(child_id, message_index):
        """Mark a message as read"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': {f'parent_messages.{message_index}.read': True}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error marking message as read: {e}")
            return False

