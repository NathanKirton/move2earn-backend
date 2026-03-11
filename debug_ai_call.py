# Quick diagnostic: call ai_insights using Flask test client with simulated session
from app import app
from database import UserDB

with app.test_client() as client:
    with client.session_transaction() as sess:
        # Simulate a child user session
        sess['user_id'] = 'test-child-id'
        sess['account_type'] = 'child'
    resp = client.get('/ai/insights/test-child-id')
    print('Status:', resp.status_code)
    try:
        print('JSON:', resp.get_json())
    except Exception as e:
        print('Body:', resp.data)
