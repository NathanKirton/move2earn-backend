# Quick Start Guide - Parent/Guardian Dashboard

## Starting the App

```bash
cd C:\Users\Nathan\Documents\Move2EarnLocal\Strava_Code
python app.py
```

Then open: `http://localhost:5000`

---

## For Parents

### 1. Create Account
- Go to `/register`
- Fill in your details
- **Check "I am a Parent/Guardian"** ✓
- Click "Create Account"

### 2. Login
- Go to `/login`
- Use your parent credentials
- You'll see the **Parent Dashboard**

### 3. Add Child
1. Fill "Add a Child" form with:
   - Child's name
   - Child's email
   - Child's password
2. Click "Create Child Account"
3. Child appears in your "Manage Your Children" section

### 4. Manage Screen Time
For each child:
- **Set Daily Limit**: Minutes per day
- **Set Weekly Limit**: Minutes per week
- **Grant Bonus**: Add minutes for good behavior/achievements

### 5. Check Game Time Balance
- **Earned**: Total minutes earned through activities
- **Used**: Minutes already spent
- **Balance**: Remaining minutes (Earned - Used)

---

## For Children

### 1. Create Account
- Go to `/register`
- Fill in your details
- **DON'T check parent checkbox**
- Click "Create Account"

### 2. Login
- Go to `/login`
- Use your email and password
- You'll see your **Child Dashboard**

### 3. Connect to Strava (Optional)
- Click "Connect Strava" button
- Authorize the app
- Activities sync automatically
- Game time earned automatically

### 4. Log Activity Manually
- Click "Manual Upload" button
- Fill in activity details:
  - Activity title
  - Date
  - Type (Run, Cycling, etc.)
  - Distance (km)
  - Duration (minutes)
  - Intensity (Easy, Medium, Hard)
- Click "Upload Activity"
- Game time is awarded instantly!

### 5. Track Your Progress
- View earned game time on dashboard
- See activity history with intensity badges
- Check your streak counter (🔥)
- Monitor available balance

---

## Game Time Calculation

When you log an activity, you earn game time based on:

```
Game Time = Distance × Intensity Multiplier

Easy     = 1.0× (1 km = 1 minute)
Medium   = 1.5× (1 km = 1.5 minutes)
Hard     = 2.0× (1 km = 2 minutes)
```

**Examples:**
- 5 km Easy run = 5 minutes
- 10 km Medium bike ride = 15 minutes
- 3 km Hard sprint = 6 minutes

---

## URL Reference

| Page | URL | Who | Purpose |
|------|-----|-----|---------|
| Landing | `/` | Everyone | App overview |
| Register | `/register | Everyone | Create account |
| Login | `/login` | Everyone | Sign in |
| Child Dashboard | `/dashboard` | Child | View activities & stats |
| Parent Dashboard | `/parent-dashboard` | Parent | Manage children |
| Upload Activity | `/upload-activity` | Child | Log activity manually |

---

## Common Tasks

### Parent: Add Bonus Time for Child
1. Go to parent dashboard
2. Find child's card
3. In "Grant Bonus Time" section:
   - Enter minutes
   - Click "Add Time"
4. Child's balance updates immediately

### Parent: Set Child's Screen Limits
1. Go to parent dashboard
2. Find child's card
3. In "Daily Limit" section:
   - Enter daily minutes (e.g., 60)
   - Enter weekly minutes (e.g., 420)
   - Click "Update Limits"

### Child: Check Available Game Time
1. Go to child dashboard
2. Look at game time card (top section)
3. Shows: "Game Time Today" with current balance
4. Parent can see full earned/used breakdown

### Child: Log a Complex Activity
**Example: 8 km hard bike ride for 50 minutes**
1. Click "Manual Upload"
2. Title: "Fast Bike Ride"
3. Date: 2025-12-05
4. Type: Cycling
5. Distance: 8 km
6. Duration: 50 minutes
7. Intensity: Hard
8. Result: 8 × 2.0 = 16 minutes earned!

---

## Troubleshooting

### Flask won't start
```bash
# Check if port 5000 is already in use
netstat -a -n -o | findstr ":5000"

# Kill the process if needed (PowerShell)
Stop-Process -Id 36500  # Replace with actual PID
```

### Child doesn't appear after adding
- Refresh the parent dashboard
- Check browser console for errors
- Verify email format is correct

### Activity upload shows error
- Verify all fields are filled
- Distance must be > 0 km
- Duration must be > 0 minutes
- Intensity must be selected

### Can't login
- Verify email and password match registration
- Check "Caps Lock" is off
- Try resetting browser cookies

---

## Features Implemented

✅ Parent and child account types
✅ Add/manage multiple children
✅ Screen time limits per child
✅ Bonus time allocation
✅ Game time tracking and balance
✅ Manual activity upload with calculations
✅ Strava integration (for children)
✅ Activity streak tracking
✅ Intensity-based badges
✅ Responsive design (mobile-friendly)

---

## API Endpoints (For Developers)

### Auth
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Parent Operations
- `POST /api/add-child` - Create child account
- `POST /api/update-child-limits/<child_id>` - Set screen time limits
- `POST /api/add-earned-time/<child_id>` - Grant bonus time
- `GET /api/get-child-balance/<child_id>` - Get child's balance

### Child Operations
- `POST /upload-activity` - Log manual activity
- `GET /api/activities` - Get activities (if Strava connected)
- `GET /api/athlete` - Get athlete info (if Strava connected)

---

## Password Requirements
- Minimum 8 characters
- Mix of uppercase and lowercase
- Numbers recommended
- Special characters recommended

---

## Data Privacy
✅ All passwords hashed with bcrypt
✅ Sessions stored locally on server
✅ No data shared between parents
✅ Each parent only sees their own children
✅ Children can't edit their own limits

---

## Contact / Support

For issues or questions about:
- **Parent Dashboard**: Check PARENT_GUIDE.md
- **Implementation Details**: Check IMPLEMENTATION_SUMMARY.md
- **Database Schema**: Check database.py comments
- **Frontend Logic**: Check JavaScript in template files

---

**Last Updated**: December 5, 2025
**Version**: 1.0.0 - Parent/Guardian Dashboard Release
