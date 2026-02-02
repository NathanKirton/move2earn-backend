import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class UserFlowTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Mock env vars
        os.environ['STRAVA_CLIENT_ID'] = 'test_id'
        os.environ['STRAVA_CLIENT_SECRET'] = 'test_secret'
        os.environ['STRAVA_REFRESH_TOKEN'] = 'test_token'
        os.environ['FLASK_SECRET_KEY'] = 'test_key'
        
        from app import app
        cls.app = app

    def setUp(self):
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['DEBUG'] = False
        self.client = self.app.test_client()

    @patch('database.UserDB.get_parent_children')
    @patch('database.UserDB.get_user_by_email')
    @patch('database.UserDB.create_user')
    @patch('database.UserDB.verify_login')
    @patch('database.UserDB.get_user_by_id')
    @patch('database.get_db')
    def test_full_user_journey(self, mock_get_db, mock_get_user, mock_verify, mock_create, mock_get_by_email, mock_get_children):
        """
        Simulate a user: Register -> Login -> View Dashboard -> Upload Activity
        """
        # 1. Setup Mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Test User Data
        user_id = 'user_123'
        user_email = 'newuser@example.com'
        user_data = {
            '_id': user_id,
            'name': 'Integration User',
            'email': user_email,
            'account_type': 'parent',  # Parent account to see dashboard
            'password': 'hashed_secret',
            'earned_game_time': 0,
            'children': [],
            'strava_connected': False
        }
        
        # Mock Registration Checks
        # get_user_by_email must return None (Falsey) so registration proceeds
        mock_get_by_email.return_value = None
        
        # Mock Registration Success
        mock_create.return_value = (True, user_id)
        
        # Mock Login Verification
        mock_verify.return_value = user_data
        
        # Mock User Lookup (for dashboard session)
        mock_get_user.return_value = user_data

        # Mock Parent Children (return empty list for now)
        mock_get_children.return_value = []

        # 2. REGISTER
        print("\n--> Step 1: Registering new user...")
        reg_data = {
            'name': 'Integration User',
            'email': user_email,
            'password': 'securepassword',
            'confirm_password': 'securepassword',
            'account_type': 'parent'
        }
        resp = self.client.post('/register', data=reg_data, follow_redirects=True)
        # Should redirect to register page with success message or login?
        # app.py: return render_template('register.html', success='Account created...')
        # It renders the template with success message, typically 200 OK.
        self.assertEqual(resp.status_code, 200, "Registration should succeed")
        self.assertIn(b'Account created successfully', resp.data)
        
        # 3. LOGIN
        print("--> Step 2: Logging in...")
        login_data = {
            'email': user_email,
            'password': 'securepassword'
        }
        resp = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200, "Login should succeed")
        
        # 4. DASHBOARD ACCESS
        print("--> Step 3: Accessing Dashboard...")
        # Since we are parent, /dashboard redirects to /parent-dashboard
        # We need to make sure session has user_id, which login_data post should have set.
        
        resp = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(resp.status_code, 200, "Dashboard should load")
        # Check for parent dashboard specific text
        self.assertIn(b'Parent Dashboard', resp.data)

    @patch('database.UserDB.record_daily_activity')
    @patch('database.UserDB.add_earned_game_time_and_increase_limit')
    @patch('database.get_db')
    def test_upload_activity(self, mock_get_db, mock_add_time, mock_record_activity):
        """
        Simulate uploading a manual activity
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock collection insert
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_one.return_value.inserted_id = 'activity_abc'

        # Mock game time logic
        mock_add_time.return_value = True
        mock_record_activity.return_value = {'applied': True, 'reward_minutes': 5, 'streak_count': 1}

        # Setup Session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'user_123'
            sess['user_email'] = 'test@example.com'
            sess['account_type'] = 'child' # Children usually upload activities

        print("\n--> Step 4: Uploading Activity...")
        data = {
            'distance': '5.0',
            'time_minutes': '30', # Changed from duration to time_minutes based on form inspection
            'date': '2023-10-27', # Changed from activity_date
            'activity_type': 'Run',
            'intensity': 'Medium',
            'activity_title': 'Morning Run'
        }
        
        # Corrected URL to /upload-activity based on app.py
        resp = self.client.post('/upload-activity', data=data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Activity logged successfully', resp.data)

if __name__ == "__main__":
    unittest.main()
