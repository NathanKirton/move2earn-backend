from flask import Flask, render_template, request, redirect, session, jsonify
from flask_cors import CORS
from flask_session import Session
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import logging
import math
import random
from database import UserDB, hash_password
from werkzeug.utils import secure_filename

import pathlib
from bson.objectid import ObjectId
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# Allow CORS for API endpoints (adjust origins in production)
CORS(app, resources={r"/api/*": {"origins": "*"}})


# Global error handlers
@app.errorhandler(502)
def bad_gateway(error):
    """Handle 502 Bad Gateway errors"""
    logger.error(f"502 Bad Gateway error: {str(error)}")
    return render_template('register.html', error='Server error. Please try again later.'), 502


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    logger.exception(f"500 Internal Server error: {str(error)}")
    return render_template('register.html', error='Server error. Please try again later.'), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Catch all uncaught exceptions"""
    logger.exception(f"Unhandled exception: {str(e)}")
    return render_template('register.html', error='An unexpected error occurred. Please try again.'), 500


# Before request hook to ensure proper content types
@app.before_request
def set_content_type():
    """Ensure proper content types for HTML responses"""
    if request.path.startswith('/register') or request.path.startswith('/login') or request.path.startswith('/dashboard'):
        # These routes should always return HTML
        pass


STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

# Determine Strava redirect URI based on environment
# In production (Render), use RENDER_EXTERNAL_URL or construct from request; in dev, use localhost
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')
if RENDER_EXTERNAL_URL:
    REDIRECT_URI = f'{RENDER_EXTERNAL_URL}/callback'
else:
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


def get_user_strava_headers(user_id):
    """Get Strava headers for a specific user (refresh token if needed)."""
    # Fetch user's tokens from DB
    user = UserDB.get_user_by_id(user_id)
    if not user:
        return None

    access_token = user.get('strava_access_token')
    refresh_token = user.get('strava_refresh_token')
    token_expiry = user.get('strava_token_expiry')

    # If expiry exists and not expired, use current token
    try:
        if access_token and token_expiry:
            expiry_dt = datetime.fromisoformat(token_expiry)
            if datetime.now() < expiry_dt:
                return {'Authorization': f'Bearer {access_token}'}
    except Exception:
        # If parsing fails, we'll attempt refresh if refresh_token present
        pass

    # Attempt to refresh using refresh_token
    if refresh_token:
        data = {
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        try:
            resp = requests.post(STRAVA_TOKEN_URL, data=data)
            if resp.status_code == 200:
                token_data = resp.json()
                new_access = token_data.get('access_token')
                new_refresh = token_data.get('refresh_token', refresh_token)
                expires_at = datetime.fromtimestamp(token_data.get('expires_at'))
                # Persist updated tokens
                UserDB.update_strava_token(user_id, new_access, new_refresh, expires_at.isoformat())
                return {'Authorization': f'Bearer {new_access}'}
        except Exception:
            logger.exception('Failed to refresh Strava token for user %s', user_id)

    # Fallback to whatever access_token exists
    if access_token:
        return {'Authorization': f'Bearer {access_token}'}

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
    try:
        logger.info(f"Registration POST request from {request.remote_addr}")
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # All new users are created as parents (children are created via parent dashboard)
        is_parent = True
        
        logger.info(f"Registration attempt for email: {email}")
        
        # Validation
        if not all([name, email, password, confirm_password]):
            logger.warning("Registration validation failed: missing fields")
            return render_template('register.html', error='All fields are required')
        
        if password != confirm_password:
            logger.warning(f"Registration validation failed for {email}: passwords do not match")
            return render_template('register.html', error='Passwords do not match')
        
        if len(password) < 8:
            logger.warning(f"Registration validation failed for {email}: password too short")
            return render_template('register.html', error='Password must be at least 8 characters')
        
        # Check if email already exists
        existing_user = UserDB.get_user_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed for {email}: email already registered")
            return render_template('register.html', error='Email already registered')
        
        logger.info(f"Creating new user: {email}")
        # Create new user (always as parent)
        success, result = UserDB.create_user(email, password, name, is_parent=is_parent)
        if success:
            logger.info(f"User created successfully: {email}")
            return render_template('register.html', success='Account created successfully! You can now login.')
        
        logger.error(f"User creation failed for {email}: {result}")
        return render_template('register.html', error=result)
    
    except Exception as e:
        logger.exception(f"Error during registration: {str(e)}")
        error_msg = 'Server error: Unable to process registration. Please try again later.'
        if 'MONGODB_URI' in str(e) or 'connection' in str(e).lower():
            error_msg = 'Database connection error. Please check that the server is properly configured and try again.'
        return render_template('register.html', error=error_msg), 500


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


@app.route('/friends')
def friends_page():
    """Display friends page"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('friends.html')


@app.route('/challenges')
def challenges_page():
    """Display challenges page"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('challenges.html')


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

        def compute_earned_minutes_for_strava(distance_km, duration_minutes, avg_hr=None, max_hr=None, pace_min_per_km=None, type_label=None):
            # Normalize inputs
            try:
                d = float(distance_km)
            except Exception:
                d = 0.0
            try:
                t = float(duration_minutes)
            except Exception:
                t = 0.0

            # Compute pace if not provided
            if pace_min_per_km is None:
                if d > 0:
                    pace = t / d
                else:
                    pace = 999
            else:
                pace = pace_min_per_km

            # Heart-rate based multiplier using chosen thresholds
            hr_mul = None
            try:
                if avg_hr is not None:
                    avg_hr_f = float(avg_hr)
                    if avg_hr_f < 150:
                        hr_mul = 1.0
                    elif avg_hr_f > 170:
                        hr_mul = 2.0
                    else:
                        hr_mul = 1.5
            except Exception:
                hr_mul = None

            # Pace bonus: faster pace gives small bonus
            pace_bonus = 0.0
            if pace < 5:
                pace_bonus = 0.5
            elif pace < 6.5:
                pace_bonus = 0.2

            # Intensity multiplier fallback
            intensity_mul = 1.0
            # Optional: weight by type (running vs cycling)
            if type_label:
                tlabel = type_label.lower()
                if 'run' in tlabel:
                    intensity_mul = 1.0
                elif 'ride' in tlabel:
                    intensity_mul = 0.8

            # Combine factors
            if hr_mul is not None:
                earned = (d * hr_mul) + (t * 0.05) + (d * pace_bonus)
            else:
                earned = (d * intensity_mul) + (t * 0.03) + (d * pace_bonus)

            earned_minutes = max(1, int(math.floor(earned)))
            return earned_minutes

        def compute_intensity_label(avg_hr=None, pace_min_per_km=None):
            # Prefer HR thresholds if available
            try:
                if avg_hr is not None:
                    avg_hr_f = float(avg_hr)
                    if avg_hr_f < 150:
                        return 'Easy'
                    if avg_hr_f > 170:
                        return 'Hard'
                    return 'Medium'
            except Exception:
                pass

            # Fallback to pace-based labels
            try:
                if pace_min_per_km is not None:
                    pace = float(pace_min_per_km)
                    if pace < 5:
                        return 'Hard'
                    if pace < 6.5:
                        return 'Medium'
                    return 'Easy'
            except Exception:
                pass

            return 'Easy'

        for activity in activities:
            dist_km = round(activity.get('distance', 0) / 1000, 2)
            moving_time = activity.get('moving_time', 0)
            duration_minutes = moving_time / 60.0 if moving_time else 0
            pace = None
            if dist_km > 0:
                # pace in min/km
                pace = (moving_time / 60.0) / dist_km

            avg_hr = activity.get('average_heartrate')
            max_hr = activity.get('max_heartrate')
            intensity_label = compute_intensity_label(avg_hr=avg_hr, pace_min_per_km=pace)
            earned = compute_earned_minutes_for_strava(dist_km, duration_minutes, avg_hr=avg_hr, max_hr=max_hr, pace_min_per_km=pace, type_label=activity.get('type'))

            formatted_activities.append({
                'id': activity['id'],
                'name': activity['name'],
                'type': activity.get('sport_type', activity.get('type')),
                'distance': dist_km,
                'moving_time': activity['moving_time'],
                'elapsed_time': activity['elapsed_time'],
                'total_elevation_gain': activity.get('total_elevation_gain', 0),
                'start_date': activity['start_date'],
                'average_speed': round(activity.get('average_speed', 0) * 3.6, 2),
                'max_speed': round(activity.get('max_speed', 0) * 3.6, 2),
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'kilojoules': activity.get('kilojoules'),
                'device_name': activity.get('device_name'),
                'trainer': activity.get('trainer', False),
                'intensity': intensity_label,
                'earned_minutes': earned
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
                          parent_email=session.get('email'),
                          children=children)


@app.route('/api/parent-children')
def api_parent_children():
    """Return parent's children data as JSON for live updates"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    children = UserDB.get_parent_children(session['user_id'])
    return jsonify({'children': children}), 200


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


# ------------------------
# Friend Requests & Approvals
# ------------------------
@app.route('/api/friend-request', methods=['POST'])
def api_friend_request():
    """Child sends a friend request to another child via email."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    to_email = data.get('email')
    if not to_email:
        return jsonify({'error': 'Email is required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    users = db['users']
    friend_requests = db['friend_requests']

    # Try to resolve to_user_id if exists
    to_user = users.find_one({'email': to_email})
    to_user_id = str(to_user['_id']) if to_user else None

    req_doc = {
        'from_user_id': session['user_id'],
        'to_user_id': to_user_id,
        'to_email': to_email,
        'status': 'pending',
        'created_at': datetime.utcnow()
    }
    res = friend_requests.insert_one(req_doc)

    return jsonify({'success': True, 'request_id': str(res.inserted_id)}), 201


@app.route('/api/parent-friend-approvals')
def api_parent_friend_approvals():
    """Return pending friend requests involving this parent's children"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    users = db['users']
    friend_requests = db['friend_requests']

    # Get parent children IDs
    parent = users.find_one({'_id': ObjectId(session['user_id'])})
    children = parent.get('children', []) if parent else []
    child_ids = [str(c) for c in children]

    # Find requests where either from_user_id or to_user_id is one of these children and status pending
    pending = list(friend_requests.find({'status': 'pending', '$or': [{'from_user_id': {'$in': child_ids}}, {'to_user_id': {'$in': child_ids}}]}))

    # Normalize
    out = []
    for p in pending:
        p['id'] = str(p['_id'])
        p['from_user_id'] = p.get('from_user_id')
        p['to_user_id'] = p.get('to_user_id')
        p['to_email'] = p.get('to_email')
        p['created_at'] = p.get('created_at').isoformat() if p.get('created_at') else None
        del p['_id']
        out.append(p)

    return jsonify({'requests': out}), 200


@app.route('/api/respond-friend-request', methods=['POST'])
def api_respond_friend_request():
    """Parent approves or rejects a pending friend request for their child."""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    req_id = data.get('request_id')
    action = data.get('action')  # 'approve' or 'reject'
    if not req_id or action not in ('approve', 'reject'):
        return jsonify({'error': 'Invalid parameters'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    friend_requests = db['friend_requests']
    users = db['users']

    try:
        fr = friend_requests.find_one({'_id': ObjectId(req_id)})
        if not fr:
            return jsonify({'error': 'Request not found'}), 404

        # Ensure parent is owner of at least one child in the request
        parent = users.find_one({'_id': ObjectId(session['user_id'])})
        children = [str(c) for c in parent.get('children', [])]
        if not (fr.get('from_user_id') in children or (fr.get('to_user_id') and fr.get('to_user_id') in children)):
            return jsonify({'error': 'Not authorized for this request'}), 403

        if action == 'reject':
            friend_requests.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'rejected', 'responded_at': datetime.utcnow()}})
            return jsonify({'success': True}), 200

        # Approve: set status and add friends to both users (if both exist)
        friend_requests.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'approved', 'responded_at': datetime.utcnow()}})
        from_id = fr.get('from_user_id')
        to_id = fr.get('to_user_id')

        # If to_user_id is unknown (email-only) we do nothing further until that user registers
        if from_id and to_id:
            users.update_one({'_id': ObjectId(from_id)}, {'$addToSet': {'friends': ObjectId(to_id)}})
            users.update_one({'_id': ObjectId(to_id)}, {'$addToSet': {'friends': ObjectId(from_id)}})

        return jsonify({'success': True}), 200
    except Exception as e:
        logger.exception('Error responding to friend request: %s', e)
        return jsonify({'error': 'Server error'}), 500


# ------------------------
# Leaderboard
# ------------------------
@app.route('/api/leaderboard')
def api_leaderboard():
    """Return top children across the app by earned game time."""
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    users = db['users']
    # Select children accounts
    top = list(users.find({'account_type': 'child'}).sort('earned_game_time', -1).limit(10))
    out = []
    for u in top:
        out.append({
            'id': str(u['_id']),
            'name': u.get('name', ''),
            'earned_game_time': int(u.get('earned_game_time', 0)),
            'daily_screen_time_limit': int(u.get('daily_screen_time_limit', 0))
        })
    return jsonify({'leaderboard': out}), 200


# ------------------------
# Challenges
# ------------------------
@app.route('/api/challenges', methods=['GET'])
def api_get_challenges():
    """Return list of challenges; include whether current user has unlocked each."""
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    challenges = db['challenges']
    unlocks = db['challenge_unlocks']

    all_ch = list(challenges.find().sort('created_at', -1))
    out = []
    user_id = session.get('user_id')
    for ch in all_ch:
        ch_id = str(ch['_id'])
        unlocked = False
        try:
            if user_id:
                unlocked = unlocks.find_one({'user_id': user_id, 'challenge_id': ch_id}) is not None
        except Exception:
            unlocked = False
        out.append({
            'id': ch_id,
            'title': ch.get('title'),
            'description': ch.get('description'),
            'reward_minutes': int(ch.get('reward_minutes', 0)),
            'locked': not unlocked
        })
    return jsonify({'challenges': out}), 200


@app.route('/api/request-challenge-unlock', methods=['POST'])
def api_request_challenge_unlock():
    """Child requests parent approval to unlock a challenge."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    if not challenge_id:
        return jsonify({'error': 'challenge_id required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    reqs = db['challenge_unlock_requests']
    doc = {
        'user_id': session['user_id'],
        'challenge_id': challenge_id,
        'status': 'pending',
        'created_at': datetime.utcnow()
    }
    res = reqs.insert_one(doc)
    return jsonify({'success': True, 'request_id': str(res.inserted_id)}), 201


@app.route('/api/parent-challenge-approvals')
def api_parent_challenge_approvals():
    """Return pending challenge-unlock requests for this parent's children"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    users = db['users']
    reqs = db['challenge_unlock_requests']

    parent = users.find_one({'_id': ObjectId(session['user_id'])})
    children = [str(c) for c in parent.get('children', [])]

    pending = list(reqs.find({'status': 'pending', 'user_id': {'$in': children}}))
    out = []
    for p in pending:
        out.append({'id': str(p['_id']), 'user_id': p['user_id'], 'challenge_id': p['challenge_id'], 'created_at': p.get('created_at').isoformat()})
    return jsonify({'requests': out}), 200


@app.route('/api/respond-challenge-unlock', methods=['POST'])
def api_respond_challenge_unlock():
    """Parent approves or rejects a challenge unlock request."""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    req_id = data.get('request_id')
    action = data.get('action')
    if not req_id or action not in ('approve', 'reject'):
        return jsonify({'error': 'Invalid parameters'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    reqs = db['challenge_unlock_requests']
    unlocks = db['challenge_unlocks']
    challenges = db['challenges']
    users = db['users']

    try:
        r = reqs.find_one({'_id': ObjectId(req_id)})
        if not r:
            return jsonify({'error': 'Request not found'}), 404

        # Verify parent owns child
        parent = users.find_one({'_id': ObjectId(session['user_id'])})
        children = [str(c) for c in parent.get('children', [])]
        if r.get('user_id') not in children:
            return jsonify({'error': 'Not authorized'}), 403

        if action == 'reject':
            reqs.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'rejected', 'responded_at': datetime.utcnow()}})
            return jsonify({'success': True}), 200

        # Approve: create unlock record and mark request approved
        reqs.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'approved', 'responded_at': datetime.utcnow()}})
        unlocks.insert_one({'user_id': r.get('user_id'), 'challenge_id': r.get('challenge_id'), 'unlocked_at': datetime.utcnow()})
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.exception('Error responding to challenge unlock: %s', e)
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/complete-challenge', methods=['POST'])
def api_complete_challenge():
    """Mark a challenge as completed by a child and credit reward minutes."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    if not challenge_id:
        return jsonify({'error': 'challenge_id required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    unlocks = db['challenge_unlocks']
    challenges = db['challenges']
    user_ch = db['user_challenges']

    # Check unlock
    unlocked = unlocks.find_one({'user_id': session['user_id'], 'challenge_id': challenge_id})
    if not unlocked:
        return jsonify({'error': 'Challenge locked or not approved'}), 403

    ch = challenges.find_one({'_id': ObjectId(challenge_id)})
    if not ch:
        return jsonify({'error': 'Challenge not found'}), 404

    reward = int(ch.get('reward_minutes', 0))
    # Record completion
    user_ch.insert_one({'user_id': session['user_id'], 'challenge_id': challenge_id, 'completed_at': datetime.utcnow()})

    # Credit reward minutes
    UserDB.add_earned_game_time_and_increase_limit(session['user_id'], reward)

    return jsonify({'success': True, 'reward_minutes': reward}), 200


@app.route('/api/friends')
def api_get_friends():
    """Return current user's friends and pending requests."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database unavailable'}), 500

    users = db['users']
    friend_requests = db['friend_requests']

    user = users.find_one({'_id': ObjectId(session['user_id'])})
    friends = []
    if user:
        for f in user.get('friends', []):
            try:
                fu = users.find_one({'_id': f})
                if fu:
                    friends.append({'id': str(fu['_id']), 'name': fu.get('name'), 'email': fu.get('email'), 'status': 'friend'})
            except Exception:
                pass

    # also include outgoing requests
    outgoing = list(friend_requests.find({'from_user_id': session['user_id'], 'status': 'pending'}))
    outgoing_fmt = [{'to_email': r.get('to_email'), 'id': str(r['_id'])} for r in outgoing]

    return jsonify({'friends': friends, 'outgoing_requests': outgoing_fmt}), 200


@app.route('/api/delete-child/<child_id>', methods=['POST'])
def api_delete_child(child_id):
    """API endpoint to delete a child account"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Verify the child belongs to this parent
    children = UserDB.get_parent_children(session['user_id'])
    child_ids = [str(c['id']) for c in children]
    
    if child_id not in child_ids:
        return jsonify({'error': 'Child not found or not your child'}), 404
    
    success = UserDB.delete_child(session['user_id'], child_id)
    if success:
        return jsonify({'success': True, 'message': 'Child account deleted'}), 200
    else:
        return jsonify({'error': 'Failed to delete child'}), 500


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
    # Round to nearest 0.5 minutes (30 seconds)
    minutes_used = max(0, round(elapsed_seconds / 30.0) * 0.5)
    seconds_used = max(0, int(elapsed_seconds % 60))

    # Record used time and clear timer
    UserDB.use_game_time(child_id, minutes_used)
    UserDB.set_timer_state(child_id, False, None)

    time_display = f"{minutes_used}m {seconds_used}s" if seconds_used > 0 else f"{minutes_used}m"
    msg = f"Timer stopped by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}. Recorded {time_display}."
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
    
    # Add the bonus time
    success = UserDB.add_earned_game_time_and_increase_limit(child_id, minutes)

    # Always add a notification when bonus time is granted
    if success:
        parent = UserDB.get_user_by_id(session.get('user_id'))
        parent_name = parent.get('name', 'Your Parent') if parent else 'Your Parent'
        
        # If no message provided, create a default one
        if message:
            notification_message = message
        else:
            notification_message = f'You received {minutes} bonus minutes!'
        
        UserDB.add_parent_message(child_id, parent_name, notification_message, minutes)

    if success:
        # Return updated values so the client can update UI without a reload
        child = UserDB.get_user_by_id(child_id)
        earned = child.get('earned_game_time', 0)
        limit = child.get('daily_screen_time_limit', 0)
        used = UserDB.get_current_used_including_running(child_id)
        balance = max(0, earned - used)
        return jsonify({'success': True, 'earned': earned, 'limit': limit, 'used': used, 'balance': balance}), 200
    else:
        return jsonify({'error': 'Failed to add time'}), 500


@app.route('/api/control-my-timer', methods=['POST'])
def api_control_my_timer():
    """Allow a child to start/stop their own timer."""
    if 'user_id' not in session or session.get('account_type') != 'child':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    action = data.get('action')
    if action not in ('start', 'stop'):
        return jsonify({'error': 'Invalid action'}), 400

    child_id = session['user_id']
    now = datetime.utcnow()

    if action == 'start':
        success = UserDB.set_timer_state(child_id, True, now)
        if success:
            # add a small notification message for audit
            UserDB.add_parent_message(child_id, 'Self', f'Timer started by child at {now.strftime("%Y-%m-%d %H:%M:%S UTC")}', 0)
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Failed to start timer'}), 500

    # stop
    child = UserDB.get_user_by_id(child_id)
    started_at = child.get('timer_started_at') if child else None
    if not started_at:
        UserDB.set_timer_state(child_id, False, None)
        UserDB.add_parent_message(child_id, 'Self', f'Timer stopped by child at {now.strftime("%Y-%m-%d %H:%M:%S UTC")} (no running timer found)', 0)
        return jsonify({'success': True, 'minutes_recorded': 0}), 200

    try:
        if isinstance(started_at, str):
            started_dt = datetime.fromisoformat(started_at)
        else:
            started_dt = started_at
    except Exception:
        started_dt = None

    if not started_dt:
        UserDB.set_timer_state(child_id, False, None)
        UserDB.add_parent_message(child_id, 'Self', f'Timer stopped by child at {now.strftime("%Y-%m-%d %H:%M:%S UTC")} (invalid start time)', 0)
        return jsonify({'success': True, 'minutes_recorded': 0}), 200

    elapsed_seconds = (now - started_dt).total_seconds()
    # Round to nearest 0.5 minutes (30 seconds)
    minutes_used = max(0, round(elapsed_seconds / 30.0) * 0.5)
    seconds_used = max(0, int(elapsed_seconds % 60))

    UserDB.use_game_time(child_id, minutes_used)
    UserDB.set_timer_state(child_id, False, None)
    
    time_display = f"{minutes_used}m {seconds_used}s" if seconds_used > 0 else f"{minutes_used}m"
    UserDB.add_parent_message(child_id, 'Self', f'Timer stopped by child at {now.strftime("%Y-%m-%d %H:%M:%S UTC")}. Recorded {time_display}.', 0)

    return jsonify({'success': True, 'minutes_recorded': minutes_used}), 200


@app.route('/api/get-child-balance/<child_id>', methods=['GET'])
def api_get_child_balance(child_id):
    """API endpoint to get child's game time balance"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Ensure daily used time is reset for the child if needed
    try:
        UserDB.reset_daily_used_if_needed(child_id)
    except Exception:
        # ignore reset failures and continue to return current values
        pass

    child = UserDB.get_user_by_id(child_id)
    if not child:
        return jsonify({'error': 'Child not found'}), 404

    # compute used including any running timer
    used = UserDB.get_current_used_including_running(child_id)
    earned = child.get('earned_game_time', 0)
    balance = max(0, earned - used)
    streak_count = child.get('streak_count', 0)
    streak_bonus = child.get('streak_bonus_minutes', 0)
    last_activity = child.get('last_activity_date')
    return jsonify({
        'earned': earned,
        'used': used,
        'balance': balance,
        'streak_count': streak_count,
        'streak_bonus_minutes': streak_bonus,
        'last_activity_date': last_activity
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
    
    # Reset daily used time on first read each day
    try:
        UserDB.reset_daily_used_if_needed(session['user_id'])
    except Exception:
        # ignore reset errors and continue
        pass

    user = UserDB.get_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    earned = user.get('earned_game_time', 0)
    # include running timer elapsed minutes in used
    used = UserDB.get_current_used_including_running(session['user_id'])
    balance = max(0, earned - used)
    limit = user.get('daily_screen_time_limit', 180)
    # Include streak info so client can show authoritative streak value
    streak_count = user.get('streak_count', 0)
    streak_bonus = user.get('streak_bonus_minutes', 0)
    
    # Get parent's streak settings for display calculations
    parent_id = user.get('parent_id')
    streak_settings = {'base_minutes': 5, 'increment_minutes': 2, 'cap_minutes': 60}
    if parent_id:
        try:
            streak_settings = UserDB.get_parent_streak_settings(str(parent_id))
        except Exception:
            pass

    return jsonify({
        'earned': earned,
        'used': used,
        'balance': balance,
        'limit': limit,
        'timer_running': user.get('timer_running', False),
        'timer_started_at': user.get('timer_started_at'),
        'streak_count': streak_count,
        'streak_bonus_minutes': streak_bonus,
        'streak_settings': streak_settings
    }), 200


@app.route('/api/update-child-streak/<child_id>', methods=['POST'])
def api_update_child_streak(child_id):
    """API endpoint to update child's streak count and bonus"""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    streak_count = data.get('streak_count')
    streak_bonus = data.get('streak_bonus_minutes', 0)
    
    if streak_count is None:
        return jsonify({'error': 'Missing streak_count'}), 400
    
    try:
        streak_count = int(streak_count)
        streak_bonus = int(streak_bonus)
        
        if streak_count < 0 or streak_bonus < 0:
            return jsonify({'error': 'Streak count and bonus must be non-negative'}), 400
        
        # Update streak count
        success1 = UserDB.update_child_streak(child_id, streak_count)
        # Update streak bonus
        success2 = UserDB.update_streak_bonus(child_id, streak_bonus)
        
        if success1 and success2:
            # Create notification message
            parent = UserDB.get_user_by_id(session['user_id'])
            parent_name = parent.get('name', 'Your Parent') if parent else 'Your Parent'
            now = datetime.utcnow()
            msg = f"Streak updated to {streak_count} day(s) with {streak_bonus} min/day bonus by {parent_name} at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            UserDB.add_parent_message(child_id, parent_name, msg, 0)
            
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Failed to update streak'}), 500
    except ValueError:
        return jsonify({'error': 'Invalid streak count or bonus value'}), 400
    except Exception as e:
        logger.exception(f"Error updating streak: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/get-streak-settings', methods=['GET'])
def api_get_streak_settings():
    """Return current parent's streak reward settings."""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    settings = UserDB.get_parent_streak_settings(session['user_id'])
    return jsonify({'success': True, 'settings': settings}), 200


@app.route('/api/set-streak-settings', methods=['POST'])
def api_set_streak_settings():
    """Set parent's streak reward configuration."""
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    try:
        # Convert to int and validate
        base = int(data.get('base_minutes', 5)) if data.get('base_minutes') is not None else 5
        inc = int(data.get('increment_minutes', 2)) if data.get('increment_minutes') is not None else 2
        cap = int(data.get('cap_minutes', 60)) if data.get('cap_minutes') is not None else 60
        
        # Log for debugging
        logger.debug("Setting streak settings for parent %s: base=%s, inc=%s, cap=%s", session.get('user_id'), base, inc, cap)

        # Update all values
        success = UserDB.set_parent_streak_settings(session['user_id'], base_minutes=base, increment_minutes=inc, cap_minutes=cap)
        if success:
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Failed to save settings'}), 500
    except Exception as e:
        logger.exception('Error saving streak settings')
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/apply-earned-strava/<child_id>', methods=['POST'])
def api_apply_earned_strava(child_id):
    """Apply earned minutes from recent Strava activities for a child.
    Only a parent of the child (logged-in) may call this endpoint.
    The endpoint will only apply minutes for Strava activities not already applied.
    """
    if 'user_id' not in session or session.get('account_type') != 'parent':
        return jsonify({'error': 'Unauthorized'}), 401

    # Verify that the child belongs to this parent
    parent_children = UserDB.get_parent_children(session['user_id'])
    if not any(c.get('id') == child_id for c in parent_children):
        return jsonify({'error': 'Child not found or not owned by parent'}), 403

    # Get Strava headers for the child
    child = UserDB.get_user_by_id(child_id)
    if not child:
        return jsonify({'error': 'Child not found'}), 404

    if not child.get('strava_connected'):
        return jsonify({'error': 'Child has not connected Strava'}), 400

    headers = get_user_strava_headers(child_id)
    if not headers:
        return jsonify({'error': 'Failed to obtain Strava token for child'}), 500

    # Fetch recent activities for the child
    per_page = request.json.get('per_page', 10) if request.is_json else request.form.get('per_page', 10)
    try:
        params = {'per_page': int(per_page), 'page': 1}
    except Exception:
        params = {'per_page': 10, 'page': 1}

    resp = requests.get(f'{STRAVA_API_URL}/athlete/activities', headers=headers, params=params)
    if resp.status_code != 200:
        return jsonify({'error': 'Failed to fetch activities from Strava', 'status': resp.status_code}), 502

    activities = resp.json()
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    activities_collection = db['activities']

    total_applied = 0
    applied_items = []
    total_streak_rewards = 0

    # Helper copied from earlier algorithm for fairness
    def compute_earned(distance_km, duration_minutes, avg_hr=None, max_hr=None, pace=None, type_label=None):
        try:
            d = float(distance_km)
        except Exception:
            d = 0.0
        try:
            t = float(duration_minutes)
        except Exception:
            t = 0.0

        if pace is None:
            if d > 0:
                pace_calc = t / d
            else:
                pace_calc = 999
        else:
            pace_calc = pace

        hr_mul = None
        try:
            if avg_hr is not None:
                avg_hr_f = float(avg_hr)
                if avg_hr_f < 150:
                    hr_mul = 1.0
                elif avg_hr_f > 170:
                    hr_mul = 2.0
                else:
                    hr_mul = 1.5
        except Exception:
            hr_mul = None

        pace_bonus = 0.0
        if pace_calc < 5:
            pace_bonus = 0.5
        elif pace_calc < 6.5:
            pace_bonus = 0.2

        intensity_mul = 1.0
        if type_label:
            tl = type_label.lower()
            if 'run' in tl:
                intensity_mul = 1.0
            elif 'ride' in tl:
                intensity_mul = 0.8

        if hr_mul is not None:
            earned = (d * hr_mul) + (t * 0.05) + (d * pace_bonus)
        else:
            earned = (d * intensity_mul) + (t * 0.03) + (d * pace_bonus)

        return max(1, int(math.floor(earned)))

    from datetime import datetime as dt

    for act in activities:
        act_id = str(act.get('id'))
        # Skip if already applied (check activities collection for external_id)
        existing = activities_collection.find_one({'source': 'strava_applied', 'external_id': act_id, 'user_id': child_id})
        if existing:
            continue

        dist_km = round(act.get('distance', 0) / 1000, 2)
        moving = act.get('moving_time', 0)
        duration_minutes = moving / 60.0 if moving else 0
        pace = (moving / 60.0) / dist_km if dist_km > 0 else None
        avg_hr = act.get('average_heartrate')
        intensity_label = None
        try:
            if avg_hr is not None:
                avg_hr_f = float(avg_hr)
                if avg_hr_f < 150:
                    intensity_label = 'Easy'
                elif avg_hr_f > 170:
                    intensity_label = 'Hard'
                else:
                    intensity_label = 'Medium'
        except Exception:
            intensity_label = None

        if not intensity_label:
            if pace is not None:
                if pace < 5:
                    intensity_label = 'Hard'
                elif pace < 6.5:
                    intensity_label = 'Medium'
                else:
                    intensity_label = 'Easy'
            else:
                intensity_label = 'Medium'

        earned = compute_earned(dist_km, duration_minutes, avg_hr=avg_hr, pace=pace, type_label=act.get('type'))

        # Insert record to mark applied activity
        try:
            activities_collection.insert_one({
                'user_id': child_id,
                'source': 'strava_applied',
                'external_id': act_id,
                'title': act.get('name'),
                'date': act.get('start_date'),
                'type': act.get('type'),
                'distance': dist_km,
                'time_minutes': int(math.ceil(duration_minutes)),
                'intensity': intensity_label,
                'earned_minutes': earned,
                'created_at': dt.utcnow()
            })
            # Credit earned minutes to child (and increase daily limit so it's usable)
            UserDB.add_earned_game_time_and_increase_limit(child_id, earned)
            total_applied += earned
            applied_items.append({'external_id': act_id, 'earned_minutes': earned, 'name': act.get('name')})

            # Record daily activity for streaks (will only apply once per day)
            try:
                activity_day = act.get('start_date')
                if activity_day and 'T' in activity_day:
                    activity_day = activity_day.split('T')[0]
                streak_result = UserDB.record_daily_activity(child_id, activity_date=activity_day, source='strava')
                if streak_result.get('applied') and isinstance(streak_result.get('reward_minutes', 0), int):
                    total_streak_rewards += int(streak_result.get('reward_minutes', 0))
            except Exception:
                logger.exception('Failed to record streak for activity %s', act_id)
        except Exception:
            logger.exception('Failed to apply activity %s for child %s', act_id, child_id)
            continue

    # Add a parent message summarizing the applied minutes
    if total_applied > 0:
        parent = UserDB.get_user_by_id(session['user_id'])
        parent_name = parent.get('name', 'Your Parent') if parent else 'Your Parent'
        msg = f"Applied {total_applied} minutes from Strava activities by {parent_name}"
        UserDB.add_parent_message(child_id, parent_name, msg, total_applied)

    # If any streak rewards were applied, add a message summarizing them
    if total_streak_rewards > 0:
        msg2 = f"Awarded {total_streak_rewards} minutes total from streak rewards."
        UserDB.add_parent_message(child_id, parent_name, msg2, total_streak_rewards)

    return jsonify({'applied_minutes': total_applied, 'applied_activities': applied_items, 'streak_rewards_applied': total_streak_rewards}), 200


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


@app.route('/api/manual-activities', methods=['GET'])
def api_get_manual_activities():
    """API endpoint to get manual and simulated activities for the current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    activities_collection = db['activities']
    # Get both manual and simulated activities
    activities = list(activities_collection.find(
        {'user_id': session['user_id'], 'source': {'$in': ['manual', 'simulated']}}
    ).sort('created_at', -1).limit(20))
    
    # Convert ObjectId to string
    for activity in activities:
        activity['id'] = str(activity['_id'])
        # Normalize date fields so JSON can be safely consumed by client
        try:
            if 'created_at' in activity:
                activity['created_at'] = activity['created_at'].isoformat()
        except Exception:
            pass
        # Ensure date (user-provided) is a string
        try:
            if 'date' in activity and not isinstance(activity['date'], str):
                activity['date'] = str(activity['date'])
        except Exception:
            pass
        del activity['_id']

    # Debug log how many manual activities are returned
    logger.debug(f"Returning {len(activities)} manual activities for user_id={session.get('user_id')}")
    

    return jsonify({'activities': activities}), 200


@app.route('/api/skip-strava', methods=['POST'])
def skip_strava():
    """Mark user as having skipped Strava connection"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Set a flag in the session to indicate Strava was skipped
        session['skip_strava'] = True
        session['strava_connected'] = False
        session.modified = True
        
        # Also update the user document to reflect this
        db = get_db()
        if db is not None:
            users_collection = db['users']
            users_collection.update_one(
                {'_id': ObjectId(session['user_id'])},
                {'$set': {'skip_strava': True}}
            )
        
        logger.info(f"User {session['user_id']} skipped Strava connection")
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error in skip_strava: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate-activities', methods=['POST'])
def api_simulate_activities():
    """API endpoint to generate simulated activities for testing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    count = data.get('count', 5)
    
    # Validate count
    try:
        count = int(count)
        if count < 1 or count > 100:
            return jsonify({'error': 'Count must be between 1 and 100'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid count value'}), 400
    
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    # Activity types and distances
    activity_types = ['Run', 'Ride', 'Swim', 'Walk', 'Hiking']
    intensities = ['Easy', 'Medium', 'Hard']
    
    activities_collection = db['activities']
    created_count = 0
    credited_today = 0

    for i in range(count):
        # Generate random data
        activity_type = random.choice(activity_types)
        intensity = random.choice(intensities)
        distance = round(random.uniform(2, 15), 1)  # 2-15 km

        # Choose a realistic pace/duration based on activity type
        if activity_type == 'Run':
            # pace between 4.0 and 6.5 min/km
            pace_min_per_km = round(random.uniform(4.0, 6.5), 2)
            duration_minutes = int(max(1, round(distance * pace_min_per_km)))
        elif activity_type == 'Walk':
            # pace between 8.0 and 12.0 min/km
            pace_min_per_km = round(random.uniform(8.0, 12.0), 2)
            duration_minutes = int(max(1, round(distance * pace_min_per_km)))
        elif activity_type == 'Hiking':
            # slower: 10-18 min/km
            pace_min_per_km = round(random.uniform(10.0, 18.0), 2)
            duration_minutes = int(max(1, round(distance * pace_min_per_km)))
        elif activity_type == 'Ride':
            # speed between 15 and 35 km/h
            speed_kmh = round(random.uniform(15, 35), 1)
            duration_minutes = int(max(1, round((distance / speed_kmh) * 60)))
            pace_min_per_km = round((60.0 / speed_kmh), 2)
        elif activity_type == 'Swim':
            # very slow per km (minutes per km), e.g., 20-40 min/km
            pace_min_per_km = round(random.uniform(20.0, 40.0), 2)
            duration_minutes = int(max(1, round(distance * pace_min_per_km)))
        else:
            duration_minutes = random.randint(15, 120)

        # Calculate earned minutes based on distance and duration
        base_earned = distance * 2  # 2 minutes per km

        # Intensity multiplier
        intensity_multiplier = {'Easy': 1.0, 'Medium': 1.5, 'Hard': 2.0}[intensity]
        earned_minutes = int(base_earned * intensity_multiplier)

        # Ensure first activity is always today, others random in last 30 days
        if i == 0:
            activity_date = datetime.utcnow().strftime('%Y-%m-%d')
        else:
            days_ago = random.randint(1, 30)
            activity_date = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        activity_doc = {
            'user_id': session['user_id'],
            'source': 'simulated',
            'title': f'{activity_type} #{i+1}',
            'type': activity_type,
            'distance': distance,
            'time_minutes': duration_minutes,
            'intensity': intensity,
            'earned_minutes': earned_minutes,
            'date': activity_date,
            'created_at': datetime.utcnow()
        }

        try:
            activities_collection.insert_one(activity_doc)
            created_count += 1

            # Only credit earned minutes and increase today's daily limit if activity is for today
            try:
                today_str = datetime.utcnow().strftime('%Y-%m-%d')
                if activity_doc.get('date') == today_str:
                    # Increase earned_game_time and daily_screen_time_limit for today's activity
                    try:
                        UserDB.add_earned_game_time_and_increase_limit(session['user_id'], earned_minutes)
                        credited_today += int(earned_minutes)
                    except Exception as e:
                        logger.exception("Failed to credit earned minutes for today's simulated activity: %s", e)

                    # Record daily activity for streaks/rewards (will not double-credit earned from activity)
                    try:
                        UserDB.record_daily_activity(session['user_id'], activity_date=activity_doc.get('date'), source='simulated')
                    except Exception:
                        pass
                else:
                    # For past activities, just insert the record without crediting earned time
                    pass
            except Exception:
                logger.exception('Error determining activity date for simulated credit')
        except Exception as e:
            logger.error(f"Error creating simulated activity: {e}")
            continue
    
    logger.info(f"Created {created_count} simulated activities for user {session['user_id']}; credited_today={credited_today}")
    return jsonify({'success': True, 'count': created_count, 'credited_minutes': credited_today}), 201


@app.route('/api/update-account', methods=['POST'])
def api_update_account():
    """Update current user's account (name, email, password)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    users = db['users']
    try:
        # If email provided, ensure uniqueness
        if email:
            existing = users.find_one({'email': email})
            if existing and str(existing.get('_id')) != str(session['user_id']):
                return jsonify({'error': 'Email already in use'}), 400

        update = {}
        if name:
            update['name'] = name
        if email:
            update['email'] = email
        if password:
            # Hash password before storing
            try:
                hp = hash_password(password)
                update['password'] = hp
            except Exception as e:
                logger.exception('Failed to hash password: %s', e)
                return jsonify({'error': 'Failed to update password'}), 500

        if not update:
            return jsonify({'success': True, 'message': 'Nothing to update'}), 200

        from bson import ObjectId
        res = users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': update})
        if res.matched_count:
            # Reflect name/email changes in session
            if 'name' in update:
                session['user_name'] = update['name']
            if 'email' in update:
                session['user_email'] = update['email']
            session.modified = True
            return jsonify({'success': True}), 200
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.exception('Error updating account: %s', e)
        return jsonify({'error': 'Server error'}), 500


@app.route('/upload-activity', methods=['GET', 'POST'])
def upload_activity():
    """Show or handle manual activity upload form"""
    if 'user_id' not in session:
        return redirect('/login') if request.method == 'GET' else jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        return render_template('upload_activity.html')
    
    # POST request - handle activity upload
    # Support both JSON and form data
    if request.is_json:
        data = request.get_json()
        activity_title = data.get('activity_title')
        activity_date = data.get('date')
        activity_type = data.get('activity_type')
        distance = data.get('distance')
        time_hours = data.get('time_hours', 0)
        time_minutes = data.get('time_minutes', 0)
        intensity = data.get('intensity')
        is_json_request = True
    else:
        activity_title = request.form.get('activity_title')
        activity_date = request.form.get('date')
        activity_type = request.form.get('activity_type')
        distance = request.form.get('distance')
        time_hours = request.form.get('time_hours', 0)
        time_minutes = request.form.get('time_minutes', 0)
        intensity = request.form.get('intensity')
        is_json_request = False
    
    if not all([activity_title, activity_date, activity_type, distance, intensity]):
        error = 'All fields are required'
        if is_json_request:
            return jsonify({'error': error}), 400
        return render_template('upload_activity.html', error=error)
    
    try:
        distance = float(distance)
        time_minutes_total = int(time_hours) * 60 + int(time_minutes)

        if distance <= 0 or time_minutes_total <= 0:
            error = 'Distance and time must be greater than 0'
            if is_json_request:
                return jsonify({'error': error}), 400
            return render_template('upload_activity.html', error=error)

        # Compute earned minutes using HR-aware algorithm when possible, otherwise fallback
        def compute_earned_minutes(distance_km, duration_minutes, intensity_label=None, avg_hr=None, max_hr=None, pace_min_per_km=None):
            # Normalize inputs
            d = float(distance_km)
            t = float(duration_minutes)

            # Pace in min/km
            if pace_min_per_km is None:
                pace = (t / d) if d > 0 else 999
            else:
                pace = pace_min_per_km

            # Heart-rate based multiplier
            hr_mul = None
            try:
                if avg_hr and max_hr:
                    hr_pct = float(avg_hr) / float(max_hr)
                    if hr_pct < 0.6:
                        hr_mul = 1.0
                    elif hr_pct < 0.75:
                        hr_mul = 1.5
                    else:
                        hr_mul = 2.0
            except Exception:
                hr_mul = None

            # Pace bonus: faster pace gives small bonus
            pace_bonus = 0.0
            if pace < 5:
                pace_bonus = 0.5
            elif pace < 6.5:
                pace_bonus = 0.2

            # Intensity multiplier fallback
            intensity_mul = 1.0
            if intensity_label:
                label = intensity_label.lower()
                if label == 'easy':
                    intensity_mul = 1.0
                elif label == 'medium':
                    intensity_mul = 1.5
                elif label == 'hard':
                    intensity_mul = 2.0

            # Combine factors. Base on distance with multipliers, plus small contribution from duration
            if hr_mul is not None:
                earned = (d * hr_mul) + (t * 0.05) + (d * pace_bonus)
            else:
                earned = (d * intensity_mul) + (t * 0.03) + (d * pace_bonus)

            earned_minutes = max(1, int(math.floor(earned)))
            return earned_minutes

        earned_minutes = compute_earned_minutes(distance, time_minutes_total, intensity_label=intensity)
        
        # Store activity in database
        db = get_db()
        if db is None:
            error = 'Database connection failed'
            if is_json_request:
                return jsonify({'error': error}), 500
            return render_template('upload_activity.html', error=error)
        
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
        
        # Add earned game time to user and increase their daily limit
        UserDB.add_earned_game_time_and_increase_limit(session['user_id'], earned_minutes)

        # Record daily activity for streaks (manual upload)
        try:
            streak_res = UserDB.record_daily_activity(session['user_id'], activity_date=activity_date, source='manual')
        except Exception:
            streak_res = {'applied': False}
        
        success_msg = f'Activity logged successfully! Earned {earned_minutes} minutes of game time.'
        
        if is_json_request:
            resp = {
                'success': True,
                'message': success_msg,
                'earned_minutes': earned_minutes,
                'activity_id': str(result.inserted_id)
            }
            if streak_res.get('applied'):
                resp['streak_reward_minutes'] = streak_res.get('reward_minutes', 0)
                resp['streak_count'] = streak_res.get('streak_count')
            return jsonify(resp), 201
        # Render page with optional note about streak reward
        if streak_res.get('applied'):
            success_msg += f" Also awarded {streak_res.get('reward_minutes', 0)} min for a {streak_res.get('streak_count')} day streak."
        return render_template('upload_activity.html', success=success_msg)
    
    except ValueError:
        error = 'Invalid distance or time value'
        if is_json_request:
            return jsonify({'error': error}), 400
        return render_template('upload_activity.html', error=error)
    except Exception as e:
        logger.exception('Error uploading activity')
        error = f'Error saving activity: {str(e)}'
        if is_json_request:
            return jsonify({'error': error}), 500
        return render_template('upload_activity.html', error=error)


# Helper function to get db instance
def get_db():
    from database import get_db as db_get_db
    return db_get_db()


if __name__ == '__main__':
    # Production-friendly run: read port from environment and bind to 0.0.0.0
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host='0.0.0.0', port=port)
