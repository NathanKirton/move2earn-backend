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
