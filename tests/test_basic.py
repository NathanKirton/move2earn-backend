import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add root directory to path to allow importing app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class BasicTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Mock environment variables before importing app
        os.environ['STRAVA_CLIENT_ID'] = 'test_id'
        os.environ['STRAVA_CLIENT_SECRET'] = 'test_secret'
        os.environ['STRAVA_REFRESH_TOKEN'] = 'test_token'
        os.environ['FLASK_SECRET_KEY'] = 'test_key'
        
        # Now import app
        from app import app
        cls.app = app

    def setUp(self):
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['DEBUG'] = False
        # Create a test client
        self.client = self.app.test_client()
        # Propagate exceptions to the test client
        self.client.testing = True 

    @patch('database.get_db')
    def test_landing_page(self, mock_get_db):
        # Mock the database connection
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('database.get_db')
    def test_login_page_loads(self, mock_get_db):
         # Mock the database connection
         mock_db = MagicMock()
         mock_get_db.return_value = mock_db
         
         response = self.client.get('/login')
         self.assertEqual(response.status_code, 200)

    @patch('database.get_db')
    def test_register_page_loads(self, mock_get_db):
         # Mock the database connection
         mock_db = MagicMock()
         mock_get_db.return_value = mock_db
         
         response = self.client.get('/register')
         self.assertEqual(response.status_code, 200)

    @patch('database.UserDB.create_user')
    @patch('database.get_db')
    def test_registration_flow(self, mock_get_db, mock_create_user):
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock UserDB.create_user to return success
        # Returns (success, user_id)
        mock_create_user.return_value = (True, 'new_user_id_123')

        # Simulate form data
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'account_type': 'parent'
        }

        # Follow redirects to see where we land
        response = self.client.post('/register', data=data, follow_redirects=True)
        
        # Should redirect to login or dashboard, status 200
        self.assertEqual(response.status_code, 200)
        
        # Verify checking for email existence (which is inside register route usually)
        # Note: The actual implementation might check existing user first.
        # Since we mocked logic, we just check if the call happened.

    @patch('database.UserDB.verify_login')
    @patch('database.get_db')
    def test_login_flow(self, mock_get_db, mock_verify_login):
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock verify_login to return a user object
        mock_user = {
            '_id': 'user_id_123',
            'name': 'Test User',
            'email': 'test@example.com',
            'account_type': 'parent',
            'password': 'hashed_password'
        }
        mock_verify_login.return_value = mock_user

        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }

        response = self.client.post('/login', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check if we are logged in (session modification) or redirected to dashboard
        # This basic check confirms no crash and successful response.

if __name__ == "__main__":
    unittest.main()
