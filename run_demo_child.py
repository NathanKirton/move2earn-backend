import requests

BASE = 'http://127.0.0.1:5000'
PARENT_EMAIL = 'demo_parent@example.local'
PARENT_PASSWORD = 'password123'
CHILD_EMAIL = 'demo_child@example.local'
CHILD_PASSWORD = 'childpass'
CHILD_NAME = 'Demo Child'

s = requests.Session()
print('Logging in as parent...')
r = s.post(f'{BASE}/login', data={'email': PARENT_EMAIL, 'password': PARENT_PASSWORD})
print('Parent login:', r.status_code)

print('Creating child account...')
r = s.post(f'{BASE}/api/add-child', json={'child_name': CHILD_NAME, 'child_email': CHILD_EMAIL, 'child_password': CHILD_PASSWORD})
print('Add child status:', r.status_code, r.text)

print('Logging out parent and logging in as child...')
# Simple logout (link exists)
s.get(f'{BASE}/logout')
# login as child
r = s.post(f'{BASE}/login', data={'email': CHILD_EMAIL, 'password': CHILD_PASSWORD})
print('Child login status:', r.status_code)

print('Fetching child dashboard...')
resp = s.get(f'{BASE}/dashboard')
print('Dashboard status:', resp.status_code)
found = 'AI Training Partner' in resp.text or 'AI/ML' in resp.text or 'AI Training' in resp.text
print('AI panel found in HTML:', found)

print('Requesting recommendation via API (empty user_id)...')
rr_empty = s.post(f'{BASE}/api/recommendations', json={'user_id': ''})
print('Empty user_id request status:', rr_empty.status_code, rr_empty.text[:300])
uid = None
if "const CHILD_ID = '" in resp.text or 'const CHILD_ID = "' in resp.text:
    # find the JS injection
    import re
    m = re.search(r"const CHILD_ID = ['\"]([^'\"]+)['\"]", resp.text)
    if m:
        uid = m.group(1)
        print('Found CHILD_ID in page:', uid)
        rr = s.post(f'{BASE}/api/recommendations', json={'user_id': uid})
        print('/api/recommendations status:', rr.status_code)
        print('body:', rr.text[:800])
else:
    print('user_id not found in page')

print('Done')
