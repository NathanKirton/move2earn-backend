````markdown
# Move2Earn — Parent-Child Game Time Management System

Move2Earn is a **family-friendly platform** that rewards children with earned gaming minutes based on physical activities. Parents set rules and limits; children earn minutes by running, cycling, swimming, or other activities tracked via Strava; and the system automatically calculates rewards, maintains streaks, and manages screen time balances.

**Live at:** https://move2earn.uk/

## 🎯 Key Features

- 🔐 **Parent & Child Accounts** — Separate roles with different dashboards and controls
- 🎮 **Game Time Rewards** — Children earn minutes by completing physical activities
- 📊 **Activity Dashboard** — View earned time, used time, and current balance
- 🔥 **Streak System** — Consecutive day bonuses encourage daily activity
- 💪 **Strava Integration** — Optional auto-sync of activities via Strava API
- 👨‍👩‍👧 **Parent Controls** — Set daily/weekly limits, grant bonus time, send messages
- 💬 **Parent-Child Messaging** — Send encouragement with bonus time awards
- 📈 **Activity Tracking** — Manual entry or Strava API for activity records
- 📱 **Responsive Design** — Works on desktop, tablet, and mobile

## 🚀 Getting Started

### Visit the App

1. **Open** https://move2earn.uk/
2. **Register** — Create a parent or child account
3. **Parent?** Check "I am a Parent/Guardian" during registration
4. **Child?** Leave unchecked; have your parent add you from their dashboard

### For Parents

1. **Create Account** — Register with your email and password
2. **Add Child** — Use parent dashboard to create child accounts
3. **Set Limits** — Configure daily and weekly screen time limits
4. **Monitor** — Track earned vs. used game time per child
5. **Reward** — Grant bonus time with encouraging messages

### For Children

1. **Create Account** — Your parent can create your account from their dashboard
2. **Log Activities** — Upload activities manually OR connect Strava
3. **Earn Time** — Get gaming minutes based on distance and intensity
4. **Check Balance** — View game time earned, used, and available
5. **Build Streaks** — Stay active daily for streak bonuses!

## 📱 Dashboard Overview

### Parent Dashboard
- **Manage Children** — View all your children's accounts
- **Game Time Tracking** — See earned, used, and balance per child
- **Limit Controls** — Set daily and weekly screen time caps
- **Bonus Rewards** — Award extra minutes with personalized messages
- **Account Settings** — Manage your profile and preferences

### Child Dashboard
- **Game Time Card** — Shows balance at a glance
- **Recent Activities** — List of uploaded or Strava-synced activities
- **Activity Streak** — Current consecutive day count and bonuses
- **Parent Messages** — View messages and bonuses from parent
- **Activity Upload** — Manually log activities or connect Strava

## 💰 How Game Time Works

**Formula:**
```
Earned Minutes = Distance (km) × Intensity Multiplier

Intensity Multipliers:
  Easy    = 1.0x
  Medium  = 1.5x
  Hard    = 2.0x

Example: 10 km Medium intensity activity
  = 10 × 1.5 = 15 minutes earned
```

**Streak Bonuses:**
```
Days 1-2:   1.0x (no bonus)
Days 3-5:   1.2x (20% bonus)
Days 6+:    1.5x (50% bonus)
```

## 🔗 API Endpoints

### Authentication
- `POST /register` — Create new account
- `POST /login` — Authenticate user
- `GET /logout` — End session

### Child Dashboard
- `GET /dashboard` — View child dashboard
- `GET /api/get-parent-messages` — Fetch parent messages
- `POST /api/record-activity` — Log activity and earn time

### Parent Dashboard
- `GET /parent-dashboard` — View parent control center
- `POST /api/add-child` — Create child account
- `POST /api/add-earned-time/<child_id>` — Grant bonus time with message
- `POST /api/update-child-limits/<child_id>` — Set daily/weekly limits

### Strava Integration
- `GET /strava-auth` — Initiate Strava OAuth
- `GET /callback` — OAuth callback
- `GET /api/activities` — Fetch Strava activities
- Date and time
- Distance (km)
- Duration
- Average heart rate (if available)
- Max heart rate (if available)

### Detailed Activity View
- All basic information
- Average and max speed
- Heart rate data
- Power data (average/max watts)
- Calories burned
- Description
- Device used

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **API**: Strava API v3
- **Authentication**: OAuth 2.0
- **Session Management**: Flask-Session

## Project Structure

```
Strava_Code/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── README.md             # This file
└── templates/
    ├── base.html         # Base template with header/nav
    └── dashboard.html    # Dashboard with activities
```

## Security Notes

- The application stores session data locally (filesystem)
- Tokens are refreshed automatically when expired
- For production deployment:
  - Change `FLASK_SECRET_KEY` to a secure random value
  - Use HTTPS instead of HTTP
  - Configure proper session storage (database, Redis)
  - Store secrets in environment variables, not in .env file

## Troubleshooting

### OAuth Login Issues
- Ensure your callback URL matches the registered URL in Strava settings
- Check that client ID and secret are correct
- Verify the redirect URI is `http://localhost:5000/callback`

### No Activities Displayed
- Ensure your Strava account has activities
- Check that your Strava token has valid permissions
- Verify the access token hasn't expired

### Session Issues
- Clear browser cookies and try again
- Check that the `flask_session` directory exists
- Ensure sufficient disk space for session storage

## Future Enhancements

- [ ] Export activities to CSV/PDF
- [ ] Activity statistics graphs and charts
- [ ] Segment performance tracking
- [ ] Training load analysis
- [ ] Goal setting and tracking
- [ ] Social features (following athletes)
- [ ] Activity stream visualization on maps
- [ ] Integration with other fitness platforms

## License

MIT License

## Support

For issues or questions, refer to:
- [Strava API Documentation](https://developers.strava.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

````
