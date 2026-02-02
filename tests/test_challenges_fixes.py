
import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class TestChallengeFixes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.get_db')
    @patch('app.UserDB')
    @patch('app.ObjectId')
    def test_duplicate_completion_prevention(self, mock_object_id, mock_user_db, mock_get_db):
        # Mock ObjectId to just return the string
        mock_object_id.side_effect = lambda x: x
        # Mock DB
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock session
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'child_123'
            
        # Mock user_challenges collection
        mock_user_challenges = MagicMock()
        mock_db.__getitem__.return_value = mock_user_challenges
        # Side effect for 'user_challenges'
        def db_getitem(name):
            if name == 'user_challenges': return mock_user_challenges
            return MagicMock()
        mock_db.__getitem__.side_effect = db_getitem

        # Case 1: Already completed
        mock_user_challenges.find_one.return_value = {'some': 'record'}
        
        resp = self.app.post('/api/complete-challenge', json={'challenge_id': 'ch_1'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('already completed', resp.get_json()['error'])

        # Case 2: Not completed
        mock_user_challenges.find_one.return_value = None
        # Mock unlocks finding
        mock_unlocks = MagicMock()
        mock_db.__getitem__.side_effect = lambda n: mock_unlocks if n == 'challenge_unlocks' else (mock_user_challenges if n == 'user_challenges' else MagicMock())
        mock_unlocks.find_one.return_value = {'status': 'unlocked'}
        
        # Mock challenges finding
        mock_challenges = MagicMock()
        def db_getitem_complex(name):
            if name == 'user_challenges': return mock_user_challenges
            if name == 'challenge_unlocks': return mock_unlocks
            if name == 'challenges': return mock_challenges
            return MagicMock()
        mock_db.__getitem__.side_effect = db_getitem_complex
        
        mock_challenges.find_one.return_value = {'reward_minutes': 10}
        
        resp = self.app.post('/api/complete-challenge', json={'challenge_id': 'ch_1'})
        self.assertEqual(resp.status_code, 200)

    @patch('app.get_db')
    @patch('app.UserDB')
    @patch('app.ObjectId')
    def test_percentage_reward_calculation(self, mock_object_id, mock_user_db, mock_get_db):
        mock_object_id.side_effect = lambda x: x
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'child_123'

        # Mock UserDB.get_user_by_id to return a user with limit=100
        mock_user_db.get_user_by_id.return_value = {'daily_screen_time_limit': 100}

        # Mock collections
        mock_uc = MagicMock()
        mock_uc.find_one.return_value = None # Not completed
        
        mock_ul = MagicMock()
        mock_ul.find_one.return_value = {'status': 'unlocked'} # Unlocked
        
        mock_ch = MagicMock()
        # Challenge with 50% reward
        mock_ch.find_one.return_value = {
            'reward_minutes': 0, 
            'reward_type': 'percentage', 
            'reward_value': 50 # 50% of 100 = 50 mins
        }
        
        def db_getitem(name):
            if name == 'user_challenges': return mock_uc
            if name == 'challenge_unlocks': return mock_ul
            if name == 'challenges': return mock_ch
            return MagicMock()
        mock_db.__getitem__.side_effect = db_getitem

        resp = self.app.post('/api/complete-challenge', json={'challenge_id': 'ch_perc'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        
        # Should be 50 minutes
        self.assertEqual(data['reward_minutes'], 50)
        # Verify add_earned.. was called with 50
        mock_user_db.add_earned_game_time_and_increase_limit.assert_called_with('child_123', 50)

if __name__ == '__main__':
    unittest.main()
