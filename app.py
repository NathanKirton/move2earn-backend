from flask import Flask, render_template, request, redirect, session, jsonify
from flask_session import Session
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import logging
import math
from database import UserDB
from werkzeug.utils import secure_filename
import pathlib

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')
REDIRECT_URI = 'http://localhost:5000/callback'
STRAVA_API_URL = 'https://www.strava.com/api/v3'
STRAVA_AUTH_URL = 'https://www.strava.com/oauth/authorize'
STRAVA_TOKEN_URL = 'https://www.strava.com/oauth/token'


def get_strava_access_token():
    """Get or refresh Strava access token"""
    if 'access_token' in session and 'token_expiry' in session:
        if datetime.now() < datetime.fromisoformat(session['token_expiry']):
            return session['access_token']
    
    # Refresh the token
    refresh_data = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': session.get('refresh_token', STRAVA_REFRESH_TOKEN),
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(STRAVA_TOKEN_URL, data=refresh_data)
    if response.status_code == 200:
        token_data = response.json()
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token', session.get('refresh_token'))
        session['token_expiry'] = datetime.fromtimestamp(token_data['expires_at']).isoformat()
        return token_data['access_token']
    
    return None


def get_strava_headers():
    """Get authorization headers for Strava API"""
    token = get_strava_access_token()
    if token:
        return {'Authorization': f'Bearer {token}'}
    return None


@app.route('/')
def index():
    """Home page - show landing or activities"""
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('landing.html')


@app.route('/landing')
def landing():
    """Landing page (always accessible)"""
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'GET':
        # Show login page
        if 'user_id' in session:
            return redirect('/dashboard')
        return render_template('login.html')
    
    # POST request - handle login
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return render_template('login.html', error='Email and password are required')
    
    # Verify user credentials
    user = UserDB.verify_login(email, password)
    if user:
        session['user_id'] = str(user['_id'])
        session['email'] = user['email']
        session['name'] = user.get('name', '')
        session['account_type'] = user.get('account_type', 'child')
        session['strava_connected'] = user.get('strava_connected', False)

        # If user previously connected Strava, restore tokens from DB into session
        if session.get('strava_connected'):
            # These fields may be None if not present
            access_token = user.get('strava_access_token')
            refresh_token = user.get('strava_refresh_token')
            token_expiry = user.get('strava_token_expiry')
            athlete_id = user.get('strava_id')
            athlete_name = user.get('strava_athlete_name') or user.get('name')

            if access_token:
                session['access_token'] = access_token
            if refresh_token:
                session['refresh_token'] = refresh_token
            if token_expiry:
                session['token_expiry'] = token_expiry
            if athlete_id:
                session['athlete_id'] = athlete_id
            if athlete_name:
                session['athlete_name'] = athlete_name

        # Debug: log session contents after successful login
        logger.debug(f"Session after login: {dict(session)}")
        logger.debug(f"Request cookies on login: {request.cookies}")

        return redirect('/dashboard')
    
    return render_template('login.html', error='Invalid email or password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'GET':
        # Show register page
        if 'user_id' in session:
            return redirect('/dashboard')
        return render_template('register.html')
    
    # POST request - handle registration
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    is_parent = request.form.get('is_parent') == 'on'
    
    # Validation
    if not all([name, email, password, confirm_password]):
        return render_template('register.html', error='All fields are required')
    
    if password != confirm_password:
        return render_template('register.html', error='Passwords do not match')
    
    if len(password) < 8:
        return render_template('register.html', error='Password must be at least 8 characters')
    
    # Check if email already exists
    if UserDB.get_user_by_email(email):
        return render_template('register.html', error='Email already registered')
    
    # Create new user
    success, result = UserDB.create_user(email, password, name, is_parent=is_parent)
    if success:
        return render_template('register.html', success='Account created successfully! You can now login.')
    
    return render_template('register.html', error=result)


@app.route('/strava-auth')
def strava_auth():
    """Redirect to Strava OAuth login (only for authenticated users)"""
    if 'user_id' not in session:
        return redirect('/login')
    
    auth_url = f"{STRAVA_AUTH_URL}?client_id={STRAVA_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=read,activity:read_all"
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """Handle Strava OAuth callback"""
    if 'user_id' not in session:
        return redirect('/login')
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    logger.debug(f"Callback received - Code: {code}, Error: {error}")
    
    if error:
        logger.error(f"Strava OAuth error: {error}")
        return f"<h1>Authorization Error</h1><p>{error}</p><p><a href='/dashboard'>Back to dashboard</a></p>"
    
    if not code:
        logger.error("No authorization code received")
        return "<h1>Error</h1><p>No authorization code received</p><p><a href='/dashboard'>Back to dashboard</a></p>"
    
    # Exchange code for token
    token_data = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    logger.debug(f"Requesting token from Strava with code: {code[:10]}...")
    logger.debug(f"Using Client ID: {STRAVA_CLIENT_ID}")
    
    try:
        response = requests.post(STRAVA_TOKEN_URL, data=token_data)
        logger.debug(f"Token response status: {response.status_code}")
        logger.debug(f"Token response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            session['access_token'] = data['access_token']
            session['refresh_token'] = data.get('refresh_token')
            session['token_expiry'] = datetime.fromtimestamp(data['expires_at']).isoformat()
            session['athlete_id'] = data['athlete']['id']
            session['athlete_name'] = f"{data['athlete']['firstname']} {data['athlete']['lastname']}"
            
            # Store Strava credentials in database
            UserDB.update_strava_credentials(
                session['user_id'],
                athlete_id=data['athlete']['id'],
                athlete_name=session['athlete_name'],
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token'),
                token_expiry=datetime.fromtimestamp(data['expires_at']).isoformat()
            )
            
            logger.info(f"Strava authentication successful for {session['athlete_name']}")
            session['strava_connected'] = True
            return redirect('/dashboard')
        else:
            logger.error(f"Failed to exchange code for token: {response.text}")
            return f"<h1>Authentication Failed</h1><p>Status: {response.status_code}</p><p>{response.text}</p><p><a href='/dashboard'>Back to dashboard</a></p>"
    except Exception as e:
        logger.exception(f"Error during token exchange: {str(e)}")
        return f"<h1>Error</h1><p>{str(e)}</p><p><a href='/dashboard'>Back to dashboard</a></p>"


@app.route('/dashboard')
def dashboard():
    """Display dashboard based on user account type"""
    if 'user_id' not in session:
        return redirect('/login')
    
    account_type = session.get('account_type', 'child')
    
    if account_type == 'parent':
        return redirect('/parent-dashboard')
    else:
        # Child dashboard
        return render_template('dashboard.html', 
                              athlete_name=session.get('athlete_name', session.get('name')),
                              strava_connected=session.get('strava_connected', False))


@app.route('/api/athlete')
def get_athlete():
    """API endpoint to get current athlete info"""
    if 'user_id' not in session or 'athlete_id' not in session:
        return jsonify({'error': 'Not authenticated with Strava'}), 401
    
    headers = get_strava_headers()
    if not headers:
        return jsonify({'error': 'Failed to get token'}), 401
    
    response = requests.get(f'{STRAVA_API_URL}/athlete', headers=headers)
    if response.status_code == 200:
        athlete = response.json()
        return jsonify({
            'id': athlete['id'],
            'firstname': athlete['firstname'],
            'lastname': athlete['lastname'],
            'profile_medium': athlete.get('profile_medium'),
            'city': athlete.get('city'),
            'state': athlete.get('state'),
            'country': athlete.get('country'),
            'premium': athlete.get('premium', False)
        })
    
    return jsonify({'error': 'Failed to fetch athlete'}), response.status_code


@app.route('/api/activities')
def get_activities():
    """API endpoint to get recent activities"""
    if 'user_id' not in session or 'athlete_id' not in session:
        return jsonify({'error': 'Not authenticated with Strava'}), 401
    
    headers = get_strava_headers()
    if not headers:
        return jsonify({'error': 'Failed to get token'}), 401
    
    # Get last 10 activities
    params = {
        'per_page': 10,
        'page': 1
    }
    
    response = requests.get(f'{STRAVA_API_URL}/athlete/activities', headers=headers, params=params)
    if response.status_code == 200:
        activities = response.json()
        formatted_activities = []
        
        for activity in activities:
            formatted_activities.append({
                'id': activity['id'],
                'name': activity['name'],
                'type': activity.get('sport_type', activity.get('type')),
                'distance': round(activity['distance'] / 1000, 2),  # Convert to km
                'moving_time': activity['moving_time'],
                'elapsed_time': activity['elapsed_time'],
                'total_elevation_gain': activity.get('total_elevation_gain', 0),
                'start_date': activity['start_date'],
                'average_speed': round(activity.get('average_speed', 0) * 3.6, 2),  # m/s to km/h
                'max_speed': round(activity.get('max_speed', 0) * 3.6, 2),
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'kilojoules': activity.get('kilojoules'),
                'device_name': activity.get('device_name'),
                'trainer': activity.get('trainer', False)
            })
        
        return jsonify(formatted_activities)
    
    return jsonify({'error': 'Failed to fetch activities'}), response.status_code


@app.route('/api/activity/<int:activity_id>')
def get_activity_detail(activity_id):
    """API endpoint to get detailed activity info"""
    if 'user_id' not in session or 'athlete_id' not in session:
        return jsonify({'error': 'Not authenticated with Strava'}), 401
    
    headers = get_strava_headers()
    if not headers:
        return jsonify({'error': 'Failed to get token'}), 401
    
    response = requests.get(f'{STRAVA_API_URL}/activities/{activity_id}', headers=headers)
    if response.status_code == 200:
        activity = response.json()
        return jsonify({
            'id': activity['id'],
            'name': activity['name'],
            'type': activity.get('sport_type', activity.get('type')),
            'distance': round(activity['distance'] / 1000, 2),
            'moving_time': activity['moving_time'],
            'elapsed_time': activity['elapsed_time'],
            'total_elevation_gain': activity.get('total_elevation_gain', 0),
            'start_date': activity['start_date'],
            'average_speed': round(activity.get('average_speed', 0) * 3.6, 2),
            'max_speed': round(activity.get('max_speed', 0) * 3.6, 2),
            'average_heartrate': activity.get('average_heartrate'),
            'max_heartrate': activity.get('max_heartrate'),
            'kilojoules': activity.get('kilojoules'),
            'average_watts': activity.get('average_watts'),
            'max_watts': activity.get('max_watts'),
            'calories': activity.get('calories'),
            'device_name': activity.get('device_name'),
            'description': activity.get('description', ''),
            'gear_id': activity.get('gear_id'),
            'private': activity.get('private', False)
        })
    
    return jsonify({'error': 'Failed to fetch activity'}), response.status_code


@app.route('/parent-dashboard')
def parent_dashboard():
    """Display parent/guardian dashboard"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return redirect('/dashboard')
    
    children = UserDB.get_parent_children(session['user_id'])
    return render_template('parent_dashboard.html', 
                          parent_name=session.get('name'),
                          children=children)


@app.route('/api/add-child', methods=['POST'])
def api_add_child():
    """API endpoint to add a child"""
    logger.debug(f"Add child request - session: {dict(session)}")
    logger.debug(f"user_id in session: {'user_id' in session}")
    logger.debug(f"account_type in session: {'account_type' in session}")
    logger.debug(f"account_type value: {session.get('account_type')}")
    logger.debug(f"Request cookies on add-child: {request.cookies}")
    
    if 'user_id' not in session:
        logger.error("No user_id in session")
        return jsonify({'error': 'Unauthorized - no user_id'}), 401
    
    if session.get('account_type') != 'parent':
        logger.error(f"User is not parent: {session.get('account_type')}")
        return jsonify({'error': 'Unauthorized - not parent'}), 401
    
    data = request.get_json()
    child_name = data.get('child_name')
    child_email = data.get('child_email')
    child_password = data.get('child_password')
    
    if not all([child_name, child_email, child_password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    success, result = UserDB.add_child(session['user_id'], child_email, child_password, child_name)
    if success:
        return jsonify({'success': True, 'child_id': result}), 201
    else:
        return jsonify({'error': result}), 400


@app.route('/api/update-child-limits/<child_id>', methods=['POST'])
def api_update_child_limits(child_id):
    """API endpoint to update child's screen time limits"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    daily_limit = data.get('daily_limit')
    weekly_limit = data.get('weekly_limit')

    # Fetch current child limits to produce notifications
    child_before = UserDB.get_user_by_id(child_id)
    old_daily = child_before.get('daily_screen_time_limit') if child_before else None
    old_weekly = child_before.get('weekly_screen_time_limit') if child_before else None
    
    success = UserDB.update_child_screen_time_limit(child_id, daily_limit, weekly_limit)
    if success:
        # Create messages for any changes
        parent = UserDB.get_user_by_id(session['user_id'])
        parent_name = parent.get('name', 'Your Parent') if parent else 'Your Parent'
        now = datetime.utcnow()

        if daily_limit is not None and old_daily is not None and daily_limit != old_daily:
            if daily_limit > old_daily:
                msg = f"Daily limit increased from {old_daily} to {daily_limit} minutes by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            else:
                msg = f"Daily limit decreased from {old_daily} to {daily_limit} minutes by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            UserDB.add_parent_message(child_id, parent_name, msg, 0)

        if weekly_limit is not None and old_weekly is not None and weekly_limit != old_weekly:
            if weekly_limit > old_weekly:
                msg = f"Weekly limit increased from {old_weekly} to {weekly_limit} minutes by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            else:
                msg = f"Weekly limit decreased from {old_weekly} to {weekly_limit} minutes by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            UserDB.add_parent_message(child_id, parent_name, msg, 0)

        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Failed to update limits'}), 500


@app.route('/api/control-timer/<child_id>', methods=['POST'])
def api_control_timer(child_id):
    """Parent can start/stop a child's timer from parent dashboard"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    action = data.get('action')
    if action not in ('start', 'stop'):
        return jsonify({'error': 'Invalid action'}), 400

    parent = UserDB.get_user_by_id(session['user_id'])
    parent_name = parent.get('name', 'Your Parent') if parent else 'Your Parent'
    now = datetime.utcnow()

    if action == 'start':
        success = UserDB.set_timer_state(child_id, True, now)
        if success:
            msg = f"Timer started by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            UserDB.add_parent_message(child_id, parent_name, msg, 0)
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Failed to start timer'}), 500

    # stop
    child = UserDB.get_user_by_id(child_id)
    started_at = child.get('timer_started_at') if child else None
    if not started_at:
        # Nothing to stop
        UserDB.set_timer_state(child_id, False, None)
        msg = f"Timer stopped by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')} (no running timer found)"
        UserDB.add_parent_message(child_id, parent_name, msg, 0)
        return jsonify({'success': True, 'minutes_recorded': 0}), 200

    # calculate elapsed minutes
    try:
        if isinstance(started_at, str):
            # parse string
            started_dt = datetime.fromisoformat(started_at)
        else:
            started_dt = started_at
    except Exception:
        started_dt = None

    if not started_dt:
        UserDB.set_timer_state(child_id, False, None)
        msg = f"Timer stopped by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')} (invalid start time)"
        UserDB.add_parent_message(child_id, parent_name, msg, 0)
        return jsonify({'success': True, 'minutes_recorded': 0}), 200

    elapsed_seconds = (now - started_dt).total_seconds()
    minutes_used = max(0, int(math.ceil(elapsed_seconds / 60.0)))

    # Record used time and clear timer
    UserDB.use_game_time(child_id, minutes_used)
    UserDB.set_timer_state(child_id, False, None)

    msg = f"Timer stopped by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}. Recorded {minutes_used} minutes."
    UserDB.add_parent_message(child_id, parent_name, msg, 0)

    return jsonify({'success': True, 'minutes_recorded': minutes_used}), 200


@app.route('/api/add-earned-time/<child_id>', methods=['POST'])
def api_add_earned_time(child_id):
    """API endpoint to add earned game time for a child"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    minutes = data.get('minutes', 0)
    message = data.get('message', '')
    
    if minutes < 0:
        return jsonify({'error': 'Invalid minutes value'}), 400
    
    # Add the bonus time and increase the daily limit so it adds to time-left as requested
    success = UserDB.add_earned_game_time_and_increase_limit(child_id, minutes)
    
    # Add the message if provided
    if success and message:
        parent = UserDB.get_user_by_id(session.get('user_id'))
        parent_name = parent.get('name', 'Your Parent') if parent else 'Your Parent'
        UserDB.add_parent_message(child_id, parent_name, message, minutes)
    
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Failed to add time'}), 500


@app.route('/api/get-child-balance/<child_id>', methods=['GET'])
def api_get_child_balance(child_id):
    """API endpoint to get child's game time balance"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    child = UserDB.get_user_by_id(child_id)
    if not child:
        return jsonify({'error': 'Child not found'}), 404
    
    balance = UserDB.get_child_game_time_balance(child_id)
    return jsonify({
        'earned': child.get('earned_game_time', 0),
        'used': child.get('used_game_time', 0),
        'balance': balance
    }), 200


@app.route('/api/get-parent-messages', methods=['GET'])
def api_get_parent_messages():
    """API endpoint to get parent messages for the logged-in child"""
    if 'user_id' not in session or session.get('account_type') != 'child':
        return jsonify({'error': 'Unauthorized'}), 401
    
    messages = UserDB.get_parent_messages(session['user_id'])
    return jsonify({'messages': messages}), 200


@app.route('/api/gametime-balance', methods=['GET'])
def api_gametime_balance():
    """API endpoint to get current user's game time balance"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = UserDB.get_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    earned = user.get('earned_game_time', 0)
    used = user.get('used_game_time', 0)
    balance = max(0, earned - used)
    limit = user.get('daily_screen_time_limit', 180)
    
    return jsonify({
        'earned': earned,
        'used': used,
        'balance': balance,
        'limit': limit
    }), 200


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/login')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


# --- Manual upload endpoint (saves to uploads/) ---
ALLOWED_EXTENSIONS = {'.gpx', '.tcx', '.fit'}
UPLOAD_DIR = pathlib.Path(__file__).parent / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint to upload activity file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    file_ext = pathlib.Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': 'Unsupported file type'}), 400

    try:
        filename = secure_filename(file.filename)
        save_path = UPLOAD_DIR / f"{session.get('user_id')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(str(save_path))
        logger.info(f"File uploaded: {save_path}")
        return jsonify({'success': f'File uploaded: {filename}'}), 200
    except Exception as e:
        logger.exception('Failed to save uploaded file')
        return jsonify({'error': 'Failed to save file'}), 500


@app.route('/upload-activity', methods=['GET', 'POST'])
def upload_activity():
    """Show or handle manual activity upload form"""
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('upload_activity.html')
    
    # POST request - handle activity upload
    activity_title = request.form.get('activity_title')
    activity_date = request.form.get('date')
    activity_type = request.form.get('activity_type')
    distance = request.form.get('distance')
    time_hours = request.form.get('time_hours', 0)
    time_minutes = request.form.get('time_minutes', 0)
    intensity = request.form.get('intensity')
    
    if not all([activity_title, activity_date, activity_type, distance, intensity]):
        return render_template('upload_activity.html', error='All fields are required')
    
    try:
        distance = float(distance)
        time_minutes_total = int(time_hours) * 60 + int(time_minutes)
        
        if distance <= 0 or time_minutes_total <= 0:
            return render_template('upload_activity.html', error='Distance and time must be greater than 0')
        
        # Calculate earned game time based on intensity and distance
        intensity_multipliers = {
            'Easy': 1.0,
            'Medium': 1.5,
            'Hard': 2.0
        }
        multiplier = intensity_multipliers.get(intensity, 1.0)
        
        # Calculate earned minutes: 1 minute earned per km at easy intensity
        # Scale with intensity multiplier
        earned_minutes = int(distance * multiplier)
        
        # Store activity in database
        db = get_db()
        if db is None:
            return render_template('upload_activity.html', error='Database connection failed')
        
        from datetime import datetime as dt
        activities_collection = db['activities']
        
        activity_doc = {
            'user_id': session['user_id'],
            'title': activity_title,
            'date': activity_date,
            'type': activity_type,
            'distance': distance,
            'time_minutes': time_minutes_total,
            'intensity': intensity,
            'earned_minutes': earned_minutes,
            'created_at': dt.utcnow(),
            'source': 'manual'
        }
        
        result = activities_collection.insert_one(activity_doc)
        
        # Add earned game time to user
        UserDB.add_earned_game_time(session['user_id'], earned_minutes)
        
        return render_template('upload_activity.html', 
                              success=f'Activity logged successfully! Earned {earned_minutes} minutes of game time.')
    
    except ValueError:
        return render_template('upload_activity.html', error='Invalid distance or time value')
    except Exception as e:
        logger.exception('Error uploading activity')
        return render_template('upload_activity.html', error=f'Error saving activity: {str(e)}')


# Helper function to get db instance
def get_db():
    from database import get_db as db_get_db
    return db_get_db()


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
