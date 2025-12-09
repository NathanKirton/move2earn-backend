# Parent/Guardian Dashboard - User Guide

## Overview

The Move2Earn application now supports both parent/guardian and child accounts. Parents can manage multiple children, set screen time limits, grant bonus time, and track earned game time.

## Getting Started

### Step 1: Create a Parent Account

1. Navigate to `/register`
2. Fill in your details:
   - Full Name
   - Email Address
   - Password (min 8 characters)
   - Confirm Password
3. **Check the "I am a Parent/Guardian" checkbox** ✓
4. Click "Create Account"

### Step 2: Login

1. Go to `/login`
2. Enter your parent email and password
3. You'll be automatically redirected to the **Parent Dashboard**

## Parent Dashboard Features

### Add a Child

1. On the parent dashboard, fill out the "Add a Child" form:
   - Child's Name
   - Email Address
   - Password (min 8 characters)
   - Confirm Password
2. Click "Create Child Account"
3. The child will appear in your "Manage Your Children" section

### Manage Children

Each child card displays:

#### 📱 Game Time Section
- **Earned (min)**: Total minutes earned through activities
- **Used (min)**: Total minutes already spent
- **Balance**: Remaining minutes available

#### ⏰ Daily Limits
- Set daily screen time limits per child
- Set weekly screen time limits per child
- Limits are stored and tracked

#### 🎁 Grant Bonus Time
- Add bonus minutes directly to a child's earned time
- Useful for special achievements or incentives
- Automatically updates the child's balance

### Screen Time Calculation

**Game Time Earned Formula:**
```
Earned Minutes = Distance (km) × Intensity Multiplier

Where:
- Easy = 1.0x multiplier
- Medium = 1.5x multiplier
- Hard = 2.0x multiplier

Example: A 5km Medium intensity activity = 5 × 1.5 = 7.5 minutes (rounds to 7 or 8 minutes)
```

## Child Account Features

### Register as a Child

Children **do NOT** check the parent checkbox during registration. They can register independently.

### Child Dashboard
- View personal activity stats
- See earned game time
- Access Strava connection (optional)
- View activity streak and intensity badges

### Log Activities

Children can log activities via:

1. **Manual Upload** (`/upload-activity`):
   - Activity Title
   - Date
   - Type (Run, Cycling, Swimming, Walking, Hiking)
   - Distance (km)
   - Duration (minutes)
   - Intensity (Easy, Medium, Hard)
   - System automatically calculates earned game time

2. **Strava Connection** (optional):
   - Connect Strava account for automatic activity tracking
   - Activities sync and earn game time

## Database Structure

### User Collection

**Parent Account:**
```json
{
  "email": "parent@example.com",
  "password": "bcrypt_hash",
  "name": "John Parent",
  "account_type": "parent",
  "children": ["child_id_1", "child_id_2"],
  "created_at": "2025-12-05T00:00:00Z",
  "strava_connected": false
}
```

**Child Account:**
```json
{
  "email": "child@example.com",
  "password": "bcrypt_hash",
  "name": "Emma Child",
  "account_type": "child",
  "parent_id": "parent_id",
  "earned_game_time": 45,
  "used_game_time": 20,
  "daily_screen_time_limit": 60,
  "weekly_screen_time_limit": 420,
  "created_at": "2025-12-05T00:00:00Z",
  "strava_connected": false
}
```

### Activities Collection

```json
{
  "user_id": "child_id",
  "title": "Morning Run",
  "date": "2025-12-05",
  "type": "Run",
  "distance": 5.0,
  "time_minutes": 45,
  "intensity": "Medium",
  "earned_minutes": 7,
  "created_at": "2025-12-05T08:30:00Z",
  "source": "manual"
}
```

## API Endpoints

### Parent-Only Endpoints

- `POST /api/add-child` - Add a child to parent account
- `POST /api/update-child-limits/<child_id>` - Update screen time limits
- `POST /api/add-earned-time/<child_id>` - Grant bonus time
- `GET /api/get-child-balance/<child_id>` - Get child's game time balance

### Authentication Flow

1. Register → `POST /register` (set `is_parent` flag)
2. Login → `POST /login` (returns `account_type`)
3. Dashboard redirect → `/dashboard` checks `account_type`
   - If `parent`: redirects to `/parent-dashboard`
   - If `child`: shows child dashboard

## Security Features

- **Bcrypt Password Hashing**: All passwords hashed with bcrypt (10 rounds)
- **Session-Based Auth**: Flask-Session for secure session management
- **Role-Based Access Control**: Parent endpoints check for `account_type: parent`
- **Parent Verification**: Parents can only manage their own children

## Example Workflow

### Complete Setup

1. **Parent Registration** (at `/register`):
   - Name: "Sarah Parent"
   - Email: "sarah@example.com"
   - Password: "SecurePass123"
   - ✓ Check "I am a Parent/Guardian"

2. **Login** (at `/login`):
   - Email: "sarah@example.com"
   - Password: "SecurePass123"
   - → Redirected to `/parent-dashboard`

3. **Add Child**:
   - Name: "Tommy"
   - Email: "tommy@example.com"
   - Password: "ChildPass123"
   - → Tommy's account created with parent_id linked

4. **Child Login** (at `/login`):
   - Email: "tommy@example.com"
   - Password: "ChildPass123"
   - → Redirected to `/dashboard` (child view)

5. **Child Logs Activity** (at `/upload-activity`):
   - Title: "Bike Ride"
   - Date: 2025-12-05
   - Type: Cycling
   - Distance: 8 km
   - Duration: 60 min
   - Intensity: Hard
   - System calculates: 8 × 2.0 = 16 minutes earned

6. **Parent Grants Bonus**:
   - Parent logs back in
   - Sees Tommy earned 16 minutes
   - Grants 10 minute bonus for good grade
   - Tommy now has 26 minutes available

## Troubleshooting

### Child Account Not Showing Up

- Refresh the parent dashboard page
- Check browser network tab for API errors
- Verify the child email is correct

### Game Time Not Updating

- Ensure activity form has all required fields
- Check that intensity is selected
- Distance must be > 0 and time must be > 0

### Parent Dashboard Not Loading

- Clear browser cookies
- Verify you're logged in as a parent account
- Check the parent account has `account_type: parent` in database

## Future Enhancements

- [ ] Activity history view per child
- [ ] Weekly/monthly reports for parents
- [ ] Multiple parent accounts per child
- [ ] Penalty system for missed activities
- [ ] Mobile app with notifications
- [ ] Leaderboards for friendly competition
- [ ] Achievement badges system
