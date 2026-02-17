from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'move2earn')

# Initialize MongoDB client lazily to avoid blocking on startup
client = None
db = None


def get_db():
    """Get MongoDB database connection, creating it if needed"""
    global client, db
    
    if db is not None:
        return db
    
    # Check if MongoDB URI is configured
    if not MONGODB_URI:
        logger.error("MONGODB_URI environment variable is not set")
        return None
    
    try:
        logger.info(f"Attempting to connect to MongoDB database: {MONGODB_DB_NAME}")
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,  # 10 second timeout for server selection
            connectTimeoutMS=10000,           # 10 second timeout for initial connection
            socketTimeoutMS=30000,            # 30 second timeout for socket operations
            retryWrites=True,
            maxPoolSize=10,                   # Limit connection pool size
            minPoolSize=2                     # Maintain minimum connections
        )
        # Verify connection
        client.admin.command('ping')
        db = client[MONGODB_DB_NAME]
        logger.info(f"✓ Connected to MongoDB database: {MONGODB_DB_NAME}")
        
        # Create indexes for better performance
        try:
            users_collection = db['users']
            # Create unique index on email for fast lookups and email uniqueness
            users_collection.create_index('email', unique=True)
            logger.info("✓ Created email index on users collection")
            
            activities_collection = db['activities']
            # Create index on user_id for faster queries
            activities_collection.create_index('user_id')
            logger.info("✓ Created user_id index on activities collection")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
        
        return db
    except ConnectionFailure as e:
        logger.error(f"✗ Failed to connect to MongoDB: {str(e)}")
        logger.error(f"  - Check MONGODB_URI environment variable is set correctly")
        logger.error(f"  - Check MongoDB Atlas IP whitelist includes this server")
        return None
    except Exception as e:
        logger.exception(f"✗ MongoDB Connection Error: {str(e)}")
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
        logger.debug("Creating user %s (password length %d)", email, len(password))
        logger.debug("Hashed password: %s...", hashed_password[:20])
        
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
            user_doc['used_game_time'] = 0  # Used minutes (total)
            user_doc['daily_used_minutes_today'] = 0  # Used minutes today (resets daily)
            user_doc['daily_earned_minutes_today'] = 0  # Earned minutes awarded today (resets daily)
            user_doc['last_daily_reset_date'] = datetime.utcnow().date().isoformat()  # Date of last daily reset
            user_doc['parent_messages'] = []  # Messages from parent
            user_doc['streak_count'] = 0  # Streak count
            user_doc['streak_bonus_minutes'] = 0  # Bonus minutes per day from streak
            user_doc['last_activity_date'] = None  # Date of last activity (for streak)
            user_doc['timer_running'] = False  # Is timer currently running
            user_doc['timer_started_at'] = None  # When timer was started
        
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
            logger.debug("User not found for email: %s", email)
            return None
        
        logger.debug("User found: %s", email)
        logger.debug("Password input length: %d", len(password))
        logger.debug("Hashed password in DB: %s...", user['password'][:20])
        
        if verify_password(password, user['password']):
            logger.debug("Password verification PASSED")
            return user
        
        logger.debug("Password verification FAILED")
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
            logger.exception("Error updating Strava credentials: %s", e)
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
            logger.exception("Error updating Strava token: %s", e)
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
            logger.exception("Error setting timer state: %s", e)
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
            logger.exception("Error adding child: %s", e)
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
        
        from datetime import datetime
        for child_id in children_ids:
            child = users.find_one({'_id': child_id})
            if child:
                # Compute used time including any currently running timer
                used = child.get('used_game_time', 0)
                timer_running = child.get('timer_running', False)
                timer_started = child.get('timer_started_at')
                try:
                    if timer_running and timer_started:
                        # parse timer_started if string
                        if isinstance(timer_started, str):
                            started_dt = datetime.fromisoformat(timer_started)
                        else:
                            started_dt = timer_started
                        elapsed_seconds = (datetime.utcnow() - started_dt).total_seconds()
                        elapsed_minutes = int(__import__('math').floor(elapsed_seconds / 60.0))
                        used_display = used + elapsed_minutes
                    else:
                        used_display = used
                except Exception:
                    used_display = used

                children.append({
                    'id': str(child['_id']),
                    'name': child['name'],
                    'email': child['email'],
                    'earned_game_time': child.get('earned_game_time', 0),
                    'used_game_time': used_display,
                    'daily_screen_time_limit': child.get('daily_screen_time_limit', 60),
                    'weekly_screen_time_limit': child.get('weekly_screen_time_limit', 420),
                    'timer_running': timer_running,
                    'timer_started_at': child.get('timer_started_at'),
                    'streak_count': child.get('streak_count', 0),
                    'streak_bonus_minutes': child.get('streak_bonus_minutes', 0),
                    'last_activity_date': child.get('last_activity_date')
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
            logger.exception("Error updating screen time limits: %s", e)
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
            logger.exception("Error adding earned game time: %s", e)
            return False

    @staticmethod
    def add_earned_game_time_and_increase_limit(child_id, minutes, persistent=False):
        """Add bonus game time and increase the daily limit by the same amount.

        By default the granted minutes are treated as daily-earned (they will be
        tracked in `daily_earned_minutes_today` and removed at the next daily reset).
        Set `persistent=True` to grant minutes that persist across days (e.g., challenge rewards).
        """
        database = get_db()
        if database is None:
            return False

        from bson import ObjectId
        users = database['users']

        try:
            # Build increment fields. Always increment earned_game_time and daily limit.
            inc_fields = {'earned_game_time': int(minutes), 'daily_screen_time_limit': int(minutes)}
            # If not persistent, also record these as today's earned minutes so they can be reverted at midnight
            if not persistent:
                inc_fields['daily_earned_minutes_today'] = int(minutes)

            result = users.update_one({'_id': ObjectId(child_id)}, {'$inc': inc_fields})
            return result.modified_count > 0
        except Exception as e:
            logger.exception("Error adding earned game time: %s", e)
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
            logger.exception("Error using game time: %s", e)
            return False

    @staticmethod
    def get_current_used_including_running(child_id):
        """Return used game time (minutes) including any currently running timer elapsed minutes."""
        child = UserDB.get_user_by_id(child_id)
        if not child:
            return 0

        used = child.get('used_game_time', 0)
        timer_running = child.get('timer_running', False)
        timer_started = child.get('timer_started_at')
        if not timer_running or not timer_started:
            return used

        try:
            from datetime import datetime
            # parse ISO string if needed
            if isinstance(timer_started, str):
                started_dt = datetime.fromisoformat(timer_started)
            else:
                started_dt = timer_started
            elapsed_seconds = (datetime.utcnow() - started_dt).total_seconds()
            import math
            elapsed_minutes = int(math.floor(elapsed_seconds / 60.0))
            return used + elapsed_minutes
        except Exception as e:
            logger.exception("Error computing running timer elapsed: %s", e)
            return used

    @staticmethod
    def get_child_game_time_balance(child_id):
        """Get remaining game time balance for a child"""
        child = UserDB.get_user_by_id(child_id)
        if not child:
            return 0
        
        earned = child.get('earned_game_time', 0)
        # use computed used including running timer
        used = UserDB.get_current_used_including_running(child_id)
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
            logger.exception("Error adding parent message: %s", e)
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
            logger.exception("Error marking message as read: %s", e)
            return False

    @staticmethod
    def update_child_streak(child_id, streak_count):
        """Update child's streak count"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': {'streak_count': max(0, int(streak_count))}}
            )
            # Return True if operation executed (even if value was the same and modified_count == 0)
            return True
        except Exception as e:
            logger.exception("Error updating streak count: %s", e)
            return False

    @staticmethod
    def update_streak_bonus(child_id, bonus_minutes_per_day):
        """Update child's streak bonus (minutes per day)"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            result = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': {'streak_bonus_minutes': max(0, int(bonus_minutes_per_day))}}
            )
            # Return True on success of the update operation (even if no modification was needed)
            return True
        except Exception as e:
            logger.exception("Error updating streak bonus: %s", e)
            return False

    @staticmethod
    def get_parent_streak_settings(parent_id):
        """Return parent's streak reward settings or defaults."""
        parent = UserDB.get_user_by_id(parent_id)
        if not parent:
            return {'base_minutes': 5, 'increment_minutes': 2, 'cap_minutes': 60}

        return {
            'base_minutes': int(parent.get('streak_reward_base_minutes', 5)),
            'increment_minutes': int(parent.get('streak_reward_increment_minutes', 2)),
            'cap_minutes': int(parent.get('streak_reward_cap_minutes', 60))
        }

    @staticmethod
    def set_parent_streak_settings(parent_id, base_minutes=None, increment_minutes=None, cap_minutes=None):
        """Set parent's streak reward settings."""
        database = get_db()
        if database is None:
            return False

        from bson import ObjectId
        users = database['users']
        update = {}
        if base_minutes is not None:
            update['streak_reward_base_minutes'] = int(base_minutes)
        if increment_minutes is not None:
            update['streak_reward_increment_minutes'] = int(increment_minutes)
        if cap_minutes is not None:
            update['streak_reward_cap_minutes'] = int(cap_minutes)

        if not update:
            return True

        try:
            users.update_one({'_id': ObjectId(parent_id)}, {'$set': update})
            return True
        except Exception as e:
            logger.exception("Error setting parent streak settings: %s", e)
            return False

    @staticmethod
    def record_daily_activity(child_id, activity_date=None, source='activity'):
        """Record that a child had activity on a given date, update streak and grant rewards.

        activity_date: ISO date string (YYYY-MM-DD) or None => uses UTC today.
        Returns dict with keys: applied (bool), streak_count, reward_minutes
        """
        database = get_db()
        if database is None:
            return {'applied': False, 'reason': 'db unavailable'}

        from bson import ObjectId
        from datetime import datetime, timedelta

        users = database['users']
        child = UserDB.get_user_by_id(child_id)
        if not child:
            return {'applied': False, 'reason': 'child not found'}

        # Determine the date string for the activity (YYYY-MM-DD)
        if activity_date:
            try:
                if 'T' in activity_date:
                    activity_day = activity_date.split('T')[0]
                else:
                    activity_day = activity_date
            except Exception:
                activity_day = datetime.utcnow().date().isoformat()
        else:
            activity_day = datetime.utcnow().date().isoformat()

        last_day = child.get('last_activity_date')
        current_streak = int(child.get('streak_count', 0))

        # If already recorded for this day, do nothing
        if last_day == activity_day:
            logger.debug("record_daily_activity: child=%s date=%s already recorded (last=%s)", child_id, activity_day, last_day)
            return {'applied': False, 'reason': 'already recorded', 'streak_count': current_streak, 'reward_minutes': 0}

        # Compute whether this continues streak. Normalize last_day to a date object when possible.
        last_date = None
        if last_day:
            try:
                # If stored as full ISO datetime or date string
                if isinstance(last_day, str):
                    if 'T' in last_day:
                        last_date = datetime.fromisoformat(last_day.split('T')[0]).date()
                    else:
                        last_date = datetime.fromisoformat(last_day).date()
                elif hasattr(last_day, 'date'):
                    last_date = last_day.date()
            except Exception:
                last_date = None

        # Convert activity_day to date object for comparison
        try:
            activity_date_obj = datetime.fromisoformat(activity_day).date()
        except Exception:
            activity_date_obj = datetime.utcnow().date()

        # Check if this activity is on consecutive day with last activity
        # Streak continues if activity is EXACTLY one day after last activity
        if last_date and activity_date_obj == last_date + timedelta(days=1):
            new_streak = current_streak + 1
        else:
            new_streak = 1

        # Determine reward using parent's settings if available
        parent_id = child.get('parent_id')
        settings = {'base_minutes': 5, 'increment_minutes': 2, 'cap_minutes': 60}
        if parent_id:
            try:
                settings = UserDB.get_parent_streak_settings(str(parent_id))
            except Exception:
                pass

        base = int(settings.get('base_minutes', 5))
        inc = int(settings.get('increment_minutes', 2))
        cap = int(settings.get('cap_minutes', 60))

        reward = base + (max(0, new_streak - 1) * inc)
        if cap and reward > cap:
            reward = cap

        logger.debug("record_daily_activity: Streak check - last_date=%s, activity_date=%s, consecutive=%s", last_date, activity_date_obj, bool(last_date and activity_date_obj == last_date + timedelta(days=1)))
        logger.debug("record_daily_activity: Reward calculation - base=%s, inc=%s, cap=%s, streak=%s, reward=%s", base, inc, cap, new_streak, reward)

        # Apply updates: set last_activity_date to activity_day, set streak_count, increment earned_game_time and daily limit
        try:
            logger.debug("record_daily_activity: applying update child=%s date=%s new_streak=%s reward=%s", child_id, activity_day, new_streak, reward)
            res = users.update_one(
                {'_id': ObjectId(child_id)},
                {'$set': {'last_activity_date': activity_day, 'streak_count': new_streak, 'streak_bonus_minutes': reward},
                 '$inc': {'earned_game_time': int(reward), 'daily_screen_time_limit': int(reward)}}
            )
            logger.debug("record_daily_activity: update result matched=%s modified=%s", getattr(res, 'matched_count', None), getattr(res, 'modified_count', None))

            # Add a parent message noting the streak reward for the child (from system)
            try:
                parent = None
                if parent_id:
                    parent = users.find_one({'_id': parent_id})
                parent_name = parent.get('name') if parent else 'Your Parent'
                msg = f"Earned {reward} min for {new_streak}-day streak ({activity_day})."
                users.update_one({'_id': ObjectId(child_id)}, {'$push': {'parent_messages': {'from_parent': parent_name, 'message': msg, 'bonus_minutes': reward, 'created_at': datetime.utcnow(), 'read': False}}})
            except Exception:
                pass

            return {'applied': True, 'streak_count': new_streak, 'reward_minutes': reward}
        except Exception as e:
            logger.exception("Error recording daily activity/streak: %s", e)
            return {'applied': False, 'reason': 'update failed'}

    @staticmethod
    def reset_daily_used_if_needed(child_id):
        """Reset daily used game time and timer state if day has changed.
        
        Checks if the current date is different from last_daily_reset_date.
        If so, resets:
        - daily_used_minutes_today to 0
        - timer_running to False
        - timer_started_at to None
        - last_daily_reset_date to today
        """
        database = get_db()
        if database is None:
            return
        
        from bson import ObjectId
        users = database['users']
        
        try:
            child = UserDB.get_user_by_id(child_id)
            if not child:
                return
            
            today_str = datetime.utcnow().date().isoformat()
            last_reset = child.get('last_daily_reset_date')
            
            # If last_reset is not set or is a different day, reset
            if not last_reset or str(last_reset) != today_str:
                logger.debug("reset_daily_used_if_needed: child=%s last_reset=%s today=%s - resetting", child_id, last_reset, today_str)
                
                # Reset daily usage, timer state, and track reset date
                # Also revert any earned minutes that were awarded today so they don't carry across days
                daily_earned = int(child.get('daily_earned_minutes_today', 0) or 0)
                updates = {
                    '$set': {
                        'daily_used_minutes_today': 0,
                        'timer_running': False,
                        'timer_started_at': None,
                        'last_daily_reset_date': today_str,
                        'daily_earned_minutes_today': 0
                    }
                }

                # If there were daily earned minutes, subtract them from persistent earned_game_time and daily limit
                if daily_earned > 0:
                    # Ensure we don't underflow earned_game_time or daily_screen_time_limit
                    try:
                        # Use $inc with negative values to subtract
                        users.update_one({'_id': ObjectId(child_id)}, {'$inc': {'earned_game_time': -int(daily_earned), 'daily_screen_time_limit': -int(daily_earned)}})
                    except Exception:
                        # If decrement fails, continue to at least reset daily fields
                        pass

                result = users.update_one(
                    {'_id': ObjectId(child_id)},
                    updates
                )
                
                logger.debug("reset_daily_used_if_needed: reset completed, modified=%s", getattr(result, 'modified_count', None))
        except Exception as e:
            logger.exception("Error resetting daily used time: %s", e)

    @staticmethod
    def delete_child(parent_id, child_id):
        """Delete a child account and remove from parent's children list"""
        database = get_db()
        if database is None:
            return False
        
        from bson import ObjectId
        users = database['users']
        
        try:
            # Remove child from parent's children list
            users.update_one(
                {'_id': ObjectId(parent_id)},
                {'$pull': {'children': ObjectId(child_id)}}
            )
            
            # Delete the child user account
            result = users.delete_one({'_id': ObjectId(child_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.exception("Error deleting child: %s", e)
            return False

