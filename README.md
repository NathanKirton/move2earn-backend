# Strava Activity Dashboard

A web application that connects to the Strava API and displays your recent activities with biometric data including heart rate averages, max heart rate, distance, and activity type.

## Features

- 🔐 Strava OAuth Login/Logout
- 📊 Dashboard with activity statistics
- 🏃 Recent activities list with filtering
- 💓 Heart rate data (average and max)
- 📏 Distance and elevation tracking
- ⚡ Activity type filtering (Running, Cycling, Swimming, Walking, Workouts)
- 🔍 Detailed activity view modal
- 📱 Responsive design

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The `.env` file is already set up with your Strava credentials:

```
STRAVA_CLIENT_ID=13312b64f7078def8184ad368e2c5e02edf87003
STRAVA_CLIENT_SECRET=f133150b8516de0fe598093056f54132b2dc445e
STRAVA_REFRESH_TOKEN=8f8cd4cbe45866d3333ba628a23f85a19da4d656
FLASK_SECRET_KEY=your-secret-key-change-in-production
```

**Important:** For production, change the `FLASK_SECRET_KEY` to a secure random value.

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

1. **Login**: Click the login button to authenticate with Strava
2. **View Dashboard**: After authentication, you'll see your activity statistics and recent activities
3. **Filter Activities**: Use the filter buttons to view specific activity types
4. **View Details**: Click on any activity card to see detailed information
5. **Logout**: Click the logout button to end your session

## API Endpoints

### Public Endpoints
- `GET /health` - Health check

### Protected Endpoints (Require Authentication)
- `GET /` - Home page (redirects to dashboard if logged in)
- `GET /dashboard` - Main dashboard view
- `GET /api/athlete` - Get current athlete information
- `GET /api/activities` - Get recent activities (10 most recent)
- `GET /api/activity/<id>` - Get detailed activity information

### Authentication Endpoints
- `GET /login` - Redirect to Strava OAuth
- `GET /callback` - OAuth callback handler
- `GET /logout` - Logout user

## Data Displayed

### Dashboard Statistics
- Number of recent activities
- Total distance (km)
- Average heart rate (bpm)
- Total elevation gain (m)

### Activity Cards
- Activity name
- Activity type (Run, Ride, Swim, Walk, Workout, etc.)
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
