# 🎁 Parent-Child Messaging System - Quick Reference

## ⚡ Quick Start

### Test the System in 3 Steps

1. **Create test accounts**
   ```bash
   python setup_test_accounts.py
   ```

2. **Start the app**
   ```bash
   python app.py
   ```

3. **Login and test**
   - Parent: http://localhost:5000/login
     - Email: `parent@test.com`
     - Password: `parent123`
   - Child: http://localhost:5000/login
     - Email: `child@test.com`
     - Password: `child123`

---

## 📝 Parent Workflow

1. Login to Parent Dashboard
2. Find child in "Manage Your Children"
3. Enter bonus minutes (e.g., `30`)
4. Enter optional message (e.g., `"Great job at soccer!"`)
5. Click "Add Time"
6. See "✓ Sent!" confirmation

---

## 👧 Child Workflow

1. Login to Dashboard
2. Scroll down to "Messages from Parent"
3. See message with:
   - Parent's name
   - Message text
   - Bonus minutes (green badge)
   - Timestamp

---

## 🔌 API Endpoints

### Grant Bonus Time
```
POST /api/add-earned-time/{child_id}
{
  "minutes": 30,
  "message": "Optional message"
}
```

### Get Messages
```
GET /api/get-parent-messages
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `database.py` | Message storage/retrieval functions |
| `app.py` | API endpoints for messages |
| `parent_dashboard.html` | Parent UI with message input |
| `dashboard.html` | Child UI with message display |
| `test_messaging.py` | Automated tests |
| `setup_test_accounts.py` | Create test accounts |

---

## ✅ Verified Features

- ✅ Parent sends message with bonus time
- ✅ Message stored in database
- ✅ Child receives message on dashboard
- ✅ Timestamps display correctly
- ✅ Bonus amounts show in green badge
- ✅ "No messages yet" shows when empty
- ✅ Multiple messages display in order
- ✅ Parent name shows on each message

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| Message not showing | Clear cache & refresh page |
| Unauthorized error | Log out and back in |
| Message too long | Keep under 200 characters |
| No parent option | Check browser dev console |

---

## 💾 Database Check

```bash
python debug_db.py
```
Verifies MongoDB connection and user creation.

---

## 📊 Example Messages

- "Great job at soccer practice!"
- "You've been active all week!"
- "Excellent effort on your run!"
- "Thanks for helping with chores!"
- "You earned this bonus time!"

---

**Status**: ✅ Ready to Use  
**Last Updated**: December 6, 2025
