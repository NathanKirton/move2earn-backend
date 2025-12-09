# Parent-Child Messaging System Guide

## Overview

The parent-child messaging system allows parents to send personalized messages to their children when granting bonus game time. Messages appear on the child's dashboard in the "Messages from Parent" section, creating better engagement and communication between parents and children.

## Features

### ✨ Parent Features
- **Add Message When Granting Bonus Time**: When a parent grants bonus game time in the parent dashboard, they can include an optional message (up to 200 characters)
- **Personalized Rewards**: Messages provide encouragement and context for the bonus time (e.g., "Great job on your soccer game!")

### 👧 Child Features
- **Message Feed**: The child dashboard displays all messages from parents in a dedicated "Messages from Parent" section
- **Message Details**: Each message shows:
  - Parent's name
  - The message text
  - Bonus minutes granted (if any)
  - Timestamp of when the message was sent
- **Real-time Display**: Messages load automatically when the child logs in

## How It Works

### For Parents

1. **Navigate to Parent Dashboard**: Log in as a parent account
2. **Locate a Child**: Find the child in the "Manage Your Children" section
3. **Grant Bonus Time**:
   - Enter the number of minutes in the "Grant Bonus Time" field
   - *(New)* Enter an optional message in the text area below (e.g., "Great job at soccer practice!")
   - Click "Add Time" button
4. **Message Sent**: The system will grant the bonus time and deliver the message to the child's dashboard

### For Children

1. **View Messages**: Log in to the child account and navigate to the dashboard
2. **Check "Messages from Parent" Section**: Located below the game time card
3. **Read Messages**: See all messages with timestamps and bonus amounts
4. **Stay Motivated**: Use the encouragement to stay active and earn more game time!

## Database Schema

### Updated User Document Fields

```javascript
// Child users now have this field:
parent_messages: [
  {
    from_parent: "Parent Name",
    message: "Your message text",
    bonus_minutes: 30,
    created_at: ISODate("2025-12-06T20:27:21Z"),
    read: false
  }
]
```

## API Endpoints

### Grant Bonus Time with Message

**Endpoint**: `POST /api/add-earned-time/<child_id>`

**Request**:
```json
{
  "minutes": 30,
  "message": "Great job on your soccer game today!"
}
```

**Response**:
```json
{
  "success": true
}
```

### Get Parent Messages

**Endpoint**: `GET /api/get-parent-messages`

**Response**:
```json
{
  "messages": [
    {
      "from_parent": "Sarah Johnson",
      "message": "Great job on your soccer game!",
      "bonus_minutes": 30,
      "created_at": "Sat, 06 Dec 2025 20:27:21 GMT",
      "read": false
    }
  ]
}
```

## UI Changes

### Parent Dashboard
- **Bonus Time Section**: Added a textarea field below the bonus time input for entering optional messages
- **Placeholder Text**: "Optional: Add a message (e.g., 'Great job this week!')"
- **Character Limit**: 200 characters max

### Child Dashboard
- **New Messages Section**: "Messages from Parent" card displays all messages
- **Message Styling**: 
  - Cyan left border (#00d4ff) for visual distinction
  - Green badges for bonus time amounts
  - Timestamps for each message
  - Shows "No messages yet" when empty

## Features Enabled by This System

### Parent-Child Linking
- Parents can now see real-time feedback from their children
- Children feel more connected to their parents through personalized messages
- Better context for why bonus time is awarded

### Communication Examples
- ✅ "Great job at soccer practice!"
- ✅ "Excellent effort with your homework today!"
- ✅ "You've been amazing this week, keep it up!"
- ✅ "Thanks for helping with chores, you earned this!"

## Testing

The `test_messaging.py` script validates the complete workflow:
1. Parent registration
2. Parent login
3. Child account creation
4. Bonus time grant with message
5. Child login
6. Message retrieval and display

Run tests with:
```bash
python -m tests.test_messaging
```

## Technical Details

### Database Functions
- `add_parent_message(child_id, parent_name, message, minutes=0)`: Store a message
- `get_parent_messages(child_id)`: Retrieve all messages for a child
- `mark_message_as_read(child_id, message_index)`: Mark message as read (future feature)

### JavaScript Functions (Child Dashboard)
- `loadParentMessages()`: Fetches and displays parent messages on page load
- Automatic formatting of timestamps
- Real-time message rendering

## Future Enhancements

- 📱 Push notifications when a new message arrives
- ✅ Mark messages as read functionality
- 🔔 Unread message counter
- 📌 Pin important messages
- 🎁 Message templates/quick replies for parents
- 💬 Child replies to parent messages

## Troubleshooting

**Messages not showing up?**
- Ensure the child has logged in after the message was sent
- Check browser developer console for any JavaScript errors
- Verify the child account is linked to the parent account

**API returning 401?**
- Make sure you're logged in as the correct account type
- Clear cookies/session and log in again
- Check that the session is active in Flask

**Message text cutting off?**
- Keep messages under 200 characters
- Messages longer than that will be truncated in the database

---

**Last Updated**: December 6, 2025
**Status**: ✅ Fully Implemented and Tested
