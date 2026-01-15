# Move2Earn Features

## Core Features

- **User Accounts**: Parent and child account types
- **Parent Dashboard**: Manage children, grant bonus game time, send messages
- **Child Dashboard**: Track game time, view messages, record activities
- **Game Time**: Earn time through activities, spend on screen time
- **Streaks**: Maintain activity streaks, earn bonus rewards
- **Activity Recording**: Manual activity logging with game time calculation
- **Parent Messaging**: Send personalized messages with bonus time rewards

## Setup

1. Install Python 3.11+
2. Run: `pip install -r requirements.txt`
3. Run: `python app.py`
4. Open: http://localhost:5000

## How It Works

**For Parents:**
- Register with parent account type
- Add children to account
- Grant bonus game time
- Send encouraging messages
- Set screen time limits

**For Children:**
- Register or be added by parent
- Log in to dashboard
- Record physical activities
- Earn game time
- View parent messages
- Track streak progress

## Database

MongoDB Atlas stores:
- User accounts and authentication
- Parent-child relationships
- Activity records
- Game time balances
- Messages and messaging history
- Streak information
