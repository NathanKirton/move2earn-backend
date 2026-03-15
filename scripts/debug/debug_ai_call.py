"""Quick diagnostic: call the recommendations endpoint using Flask test client."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        # Simulate a child user session
        sess['user_id'] = 'test-child-id'
        sess['account_type'] = 'child'
    resp = client.post('/api/recommendations', json={'user_id': 'test-child-id'})
    print('Status:', resp.status_code)
    try:
        print('JSON:', resp.get_json())
    except Exception:
        print('Body:', resp.data)
