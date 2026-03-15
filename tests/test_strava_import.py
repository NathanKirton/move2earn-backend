import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class StravaImportTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['STRAVA_CLIENT_ID'] = 'test_id'
        os.environ['STRAVA_CLIENT_SECRET'] = 'test_secret'
        os.environ['STRAVA_REFRESH_TOKEN'] = 'test_token'
        os.environ['FLASK_SECRET_KEY'] = 'test_key'

        from app import app
        cls.app = app

    def setUp(self):
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.requests.get')
    @patch('app.get_user_strava_headers')
    @patch('app.UserDB.add_parent_message')
    @patch('app.UserDB.record_daily_activity')
    @patch('app.UserDB.add_earned_game_time')
    @patch('app.UserDB.add_earned_game_time_and_increase_limit')
    @patch('app.UserDB.get_user_by_id')
    @patch('app.UserDB.get_parent_children')
    @patch('app.get_db')
    def test_apply_earned_strava_counts_historical_minutes(
        self,
        mock_get_db,
        mock_get_parent_children,
        mock_get_user_by_id,
        mock_add_today,
        mock_add_historical,
        mock_record_daily_activity,
        mock_add_parent_message,
        mock_get_user_strava_headers,
        mock_requests_get,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        activities_collection = MagicMock()
        mock_db.__getitem__.return_value = activities_collection
        activities_collection.find_one.return_value = None
        activities_collection.insert_one.return_value.inserted_id = 'applied1'

        parent_id = '507f1f77bcf86cd799439011'
        child_id = '507f1f77bcf86cd799439012'
        mock_get_parent_children.return_value = [{'id': child_id}]
        mock_get_user_by_id.side_effect = [
            {'_id': child_id, 'strava_connected': True},
            {'_id': parent_id, 'name': 'Parent Tester'},
        ]
        mock_get_user_strava_headers.return_value = {'Authorization': 'Bearer test'}
        mock_record_daily_activity.return_value = {'applied': False, 'reward_minutes': 0, 'streak_count': 1}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            'id': 123,
            'name': 'Historic Ride',
            'distance': 10000,
            'moving_time': 1800,
            'start_date': '2026-03-10T09:00:00Z',
            'type': 'Ride',
            'average_heartrate': 145,
        }]
        mock_requests_get.return_value = mock_resp

        with self.client.session_transaction() as sess:
            sess['user_id'] = parent_id
            sess['account_type'] = 'parent'

        response = self.client.post(f'/api/apply-earned-strava/{child_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['applied_minutes'], data['applied_activities'][0]['earned_minutes'])
        mock_add_historical.assert_called_once()
        mock_add_today.assert_not_called()
        mock_add_parent_message.assert_called()

    @patch('app.requests.get')
    @patch('app.get_user_strava_headers')
    @patch('app.UserDB.add_parent_message')
    @patch('app.UserDB.record_daily_activity')
    @patch('app.UserDB.add_earned_game_time')
    @patch('app.UserDB.add_earned_game_time_and_increase_limit')
    @patch('app.UserDB.get_user_by_id')
    @patch('app.UserDB.get_parent_children')
    @patch('app.get_db')
    def test_apply_earned_strava_accepts_empty_json_body(
        self,
        mock_get_db,
        mock_get_parent_children,
        mock_get_user_by_id,
        mock_add_today,
        mock_add_historical,
        mock_record_daily_activity,
        mock_add_parent_message,
        mock_get_user_strava_headers,
        mock_requests_get,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        activities_collection = MagicMock()
        mock_db.__getitem__.return_value = activities_collection
        activities_collection.find_one.return_value = None
        activities_collection.insert_one.return_value.inserted_id = 'applied2'

        parent_id = '507f1f77bcf86cd799439021'
        child_id = '507f1f77bcf86cd799439022'
        mock_get_parent_children.return_value = [{'id': child_id}]
        mock_get_user_by_id.side_effect = [
            {'_id': child_id, 'strava_connected': True},
            {'_id': parent_id, 'name': 'Parent Tester'},
        ]
        mock_get_user_strava_headers.return_value = {'Authorization': 'Bearer test'}
        mock_record_daily_activity.return_value = {'applied': False, 'reward_minutes': 0, 'streak_count': 1}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_requests_get.return_value = mock_resp

        with self.client.session_transaction() as sess:
            sess['user_id'] = parent_id
            sess['account_type'] = 'parent'

        response = self.client.post(f'/api/apply-earned-strava/{child_id}', json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['applied_minutes'], 0)
        mock_requests_get.assert_called_once()

    @patch('app.requests.get')
    @patch('app.get_user_strava_headers')
    @patch('app.UserDB.record_daily_activity')
    @patch('app.UserDB.add_earned_game_time')
    @patch('app.UserDB.add_earned_game_time_and_increase_limit')
    @patch('app.UserDB.get_user_by_id')
    @patch('app.UserDB.get_parent_children')
    @patch('app.get_db')
    def test_apply_earned_strava_rolls_back_marker_on_credit_failure(
        self,
        mock_get_db,
        mock_get_parent_children,
        mock_get_user_by_id,
        mock_add_today,
        mock_add_historical,
        mock_record_daily_activity,
        mock_get_user_strava_headers,
        mock_requests_get,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        activities_collection = MagicMock()
        mock_db.__getitem__.return_value = activities_collection
        activities_collection.find_one.return_value = None
        activities_collection.insert_one.return_value.inserted_id = 'applied3'

        parent_id = '507f1f77bcf86cd799439031'
        child_id = '507f1f77bcf86cd799439032'
        mock_get_parent_children.return_value = [{'id': child_id}]
        mock_get_user_by_id.side_effect = [
            {'_id': child_id, 'strava_connected': True},
            {'_id': parent_id, 'name': 'Parent Tester'},
        ]
        mock_get_user_strava_headers.return_value = {'Authorization': 'Bearer test'}
        mock_add_historical.side_effect = RuntimeError('credit failed')
        mock_record_daily_activity.return_value = {'applied': False, 'reward_minutes': 0, 'streak_count': 1}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            'id': 456,
            'name': 'Historic Run',
            'distance': 5000,
            'moving_time': 1500,
            'start_date': '2026-03-10T09:00:00Z',
            'type': 'Run',
        }]
        mock_requests_get.return_value = mock_resp

        with self.client.session_transaction() as sess:
            sess['user_id'] = parent_id
            sess['account_type'] = 'parent'

        response = self.client.post(f'/api/apply-earned-strava/{child_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['applied_minutes'], 0)
        self.assertEqual(data['applied_activities'][0]['earned_minutes'], 0)
        activities_collection.delete_one.assert_called_once()


if __name__ == '__main__':
    unittest.main()