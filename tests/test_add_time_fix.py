#!/usr/bin/env python
"""Stub placeholder — test moved to `tests/` directory.

Run the moved test with:

    python -m tests.test_add_time_fix

This file remains to avoid breaking scripts that referenced it at the old path.
"""

print("This test has moved to ./tests/test_add_time_fix.py")
print("Run it from the project root with: python -m tests.test_add_time_fix")
#!/usr/bin/env python
"""Test the Add Time button fix"""

import requests
from datetime import datetime

BASE_URL = 'http://localhost:5000'

print("\n" + "="*60)
print("TESTING ADD TIME BUTTON FIX")
print("="*60 + "\n")

timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:12]
parent_email = f'test_parent_{timestamp}@example.com'
child_email = f'test_child_{timestamp}@example.com'

# Create session
parent_session = requests.Session()

# 1. Register parent
print("1️⃣ Registering parent...")
parent_data = {
    'email': parent_email,
    'password': 'password123',
    'confirm_password': 'password123',
    'name': 'Test Parent',
    'is_parent': 'on'
}
response = parent_session.post(f'{BASE_URL}/register', data=parent_data)
print(f"   Status: {response.status_code}")

# 2. Login parent
print("\n2️⃣ Logging in as parent...")
login_data = {
    'email': parent_email,
    'password': 'password123'
}
response = parent_session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=False)
print(f"   Status: {response.status_code}")

# 3. Create child
print("\n3️⃣ Creating child account...")
child_data = {
    'child_name': 'Test Child',
    'child_email': child_email,
    'child_password': 'childpass123'
}
response = parent_session.post(f'{BASE_URL}/api/add-child', 
                               json=child_data)
data = response.json()
print(f"   Status: {response.status_code}")
if response.status_code in [200, 201]:
    child_id = data.get('child_id')
    print(f"   ✓ Child created: {child_id}")
else:
    print(f"   ✗ Failed: {data}")
    exit(1)

# 4. Test "Add Time" button
print("\n4️⃣ Testing Add Time button...")
bonus_data = {
    'minutes': 30,
    'message': 'Great job today!'
}
response = parent_session.post(f'{BASE_URL}/api/add-earned-time/{child_id}', 
                               json=bonus_data)
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Response: {data}")

if response.status_code == 200:
    print("   ✓ Add Time button works!")
else:
    print(f"   ✗ Error: {data.get('error', 'Unknown error')}")
    exit(1)

# 5. Login as child and check game time
print("\n5️⃣ Logging in as child...")
child_session = requests.Session()
child_login = {
    'email': child_email,
    'password': 'childpass123'
}
response = child_session.post(f'{BASE_URL}/login', data=child_login, allow_redirects=False)
print(f"   Status: {response.status_code}")

# 6. Check game time via API
print("\n6️⃣ Fetching game time balance...")
response = child_session.get(f'{BASE_URL}/api/gametime-balance')
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Earned: {data.get('earned')} minutes")
print(f"   Used: {data.get('used')} minutes")
print(f"   Balance: {data.get('balance')} minutes")
print(f"   Limit: {data.get('limit')} minutes")

if data.get('earned', 0) >= 30:
    print("\n   ✓ Game time was properly added!")
else:
    print("\n   ✗ Game time was not added correctly")
    exit(1)

print("\n" + "="*60)
print("✅ ADD TIME BUTTON FIX VERIFIED")
print("="*60 + "\n")
