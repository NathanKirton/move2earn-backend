# Move2Earn

Parent-child game time management system. Children earn gaming time through physical activities. Parents manage accounts and set screen time limits.

## Quick Start

1. Install Python 3.11+
2. Run: `pip install -r requirements.txt`
3. Run: `python app.py`
4. Open: http://localhost:5000

## Features

- Parent and child account types
- Game time earned through activities
- Parent dashboard to manage children
- Screen time limits
- Activity tracking
- Streak bonuses
- Parent messaging to children
- Strava integration (optional)

## Database

MongoDB Atlas cloud database. Connection configured in `.env`.

## File Structure

- `app.py` - Main application
- `database.py` - Database operations  
- `templates/` - HTML pages
- `static/` - CSS and JavaScript
- `.env` - Configuration

## For Parents

1. Register with parent account type
2. Add children from parent dashboard
3. Grant bonus game time
4. Send messages to children
5. Set screen time limits

## For Children

1. Register or be added by parent
2. Log in to dashboard
3. Record activities
4. Earn game time
5. View parent messages
6. Track streaks

## Database Management

The `db_management.py` script provides utilities for managing the MongoDB database. **Use with caution - these operations are destructive!**

### Interactive Menu

Run the tool with an interactive menu:
```bash
python db_management.py
```

This displays a menu with options to:
1. List all users
2. Delete user by email
3. Delete user by ID
4. Reset game time for a user
5. Reset all game time
6. Clear all activities
7. Clear all users

### Direct Function Usage

You can also import and call specific functions:

```python
from db_management import (
    clear_all_users,
    clear_all_activities,
    delete_user_by_email,
    reset_user_game_time,
    list_all_users
)

# Delete all users
clear_all_users()

# Delete specific user
delete_user_by_email('user@example.com')

# List all users
list_all_users()

# Reset game time for a user
reset_user_game_time('user@example.com')
```

### Available Functions

- `clear_all_users()` - Delete all user accounts (requires confirmation)
- `clear_all_activities()` - Delete all activity records (requires confirmation)
- `delete_user_by_email(email)` - Delete a specific user by email
- `delete_user_by_id(user_id)` - Delete a specific user by MongoDB ObjectId
- `reset_user_game_time(email)` - Reset game time for a specific user
- `reset_all_user_game_time()` - Reset game time for all users (requires confirmation)
- `list_all_users()` - Display all users in a formatted table

### Configuration

The tool connects to MongoDB using the `MONGODB_URI` environment variable from `.env`. It targets the `Move2EarnProject` database for user operations.
