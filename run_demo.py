import time
import requests

BASE = 'http://127.0.0.1:5000'
EMAIL = 'demo_parent@example.local'
PASSWORD = 'password123'
NAME = 'Demo Parent'

s = requests.Session()
print('Registering demo parent...')
try:
    r = s.post(f'{BASE}/register', data={'name': NAME, 'email': EMAIL, 'password': PASSWORD, 'confirm_password': PASSWORD})
    print('Register status:', r.status_code)
except Exception as e:
    print('Register request failed:', e)

print('Logging in...')
try:
    r = s.post(f'{BASE}/login', data={'email': EMAIL, 'password': PASSWORD})
    print('Login status:', r.status_code)
except Exception as e:
    print('Login request failed:', e)

print('Fetching parent dashboard...')
try:
    r = s.get(f'{BASE}/parent-dashboard')
    print('Dashboard status:', r.status_code)
    found = 'AI Training Partner' in r.text or 'AI/ML' in r.text or 'AI Training' in r.text
    print('AI panel found in HTML:', found)
    # Print a short excerpt around the panel if present
    if found:
        idx = r.text.find('AI Training Partner')
        start = max(0, idx-120)
        print(r.text[start: start+300])
    else:
        print('Panel not found; show first 400 chars of page:')
        print(r.text[:400])
except Exception as e:
    print('Dashboard request failed:', e)

print('Done')
