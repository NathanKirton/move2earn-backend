#!/usr/bin/env python
"""
Test script to verify parent-child messaging system works correctly
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = 'http://localhost:5000'

def test_messaging_system():
    """Test the complete parent-child messaging flow"""
    
    print("\n" + "="*60)
    print("TESTING PARENT-CHILD MESSAGING SYSTEM")
    print("="*60 + "\n")
    
    # Generate unique IDs for this test run
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:12]
    parent_email = f'testparent{timestamp}@example.com'
    child_email = f'testchild{timestamp}@example.com'
    
    # Create a session for the parent
    parent_session = requests.Session()
    
    # 1. Register parent account
    print("1️⃣ Registering parent account...")
    parent_data = {
        'email': parent_email,
        'password': 'password123',
        'confirm_password': 'password123',
        'name': 'Sarah Johnson',
        'is_parent': 'on'
    }
    
    response = parent_session.post(f'{BASE_URL}/register', data=parent_data)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response: {response.text[:200]}")
    
    # 2. Login as parent
    print("\n2️⃣ Logging in as parent...")
    login_data = {
        'email': parent_email,
        'password': 'password123'
    }
    
    response = parent_session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=False)
    print(f"   Status: {response.status_code}")
    print(f"   Cookies: {parent_session.cookies.get_dict()}")
    print(f"   Response URL: {response.url}")
    if response.status_code == 302:
        print(f"   Redirects to: {response.headers.get('Location')}")
    
    # 3. Create a child account via parent API
    print("\n3️⃣ Adding child account via parent API...")
    child_data = {
        'child_name': 'Emma Johnson',
        'child_email': child_email,
        'child_password': 'childpass123'
    }
    
    response = parent_session.post(
        f'{BASE_URL}/api/add-child',
        json=child_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code not in [200, 201]:
        print("   ❌ Failed to add child!")
        return
    
    child_id = response.json().get('child_id')
    print(f"   ✓ Child ID: {child_id}")
    
    # 4. Grant bonus time with a message
    print("\n4️⃣ Granting bonus time with a message...")
    bonus_data = {
        'minutes': 30,
        'message': 'Great job on your soccer game today! Keep up the amazing work!'
    }
    
    response = parent_session.post(
        f'{BASE_URL}/api/add-earned-time/{child_id}',
        json=bonus_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code != 200:
        print("   ❌ Failed to add bonus time!")
        return
    
    print("   ✓ Bonus time granted with message")
    
    # 5. Login as child and check messages
    print("\n5️⃣ Logging in as child...")
    child_session = requests.Session()
    
    child_login_data = {
        'email': child_email,
        'password': 'childpass123'
    }
    
    response = child_session.post(f'{BASE_URL}/login', data=child_login_data)
    print(f"   Status: {response.status_code}")
    
    # 6. Fetch parent messages via API
    print("\n6️⃣ Fetching parent messages...")
    response = child_session.get(
        f'{BASE_URL}/api/get-parent-messages',
        headers={'Content-Type': 'application/json'}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2, default=str)}")
    
    if response.status_code == 200:
        messages = response.json().get('messages', [])
        if messages:
            msg = messages[0]
            print(f"\n   ✓ Message received!")
            print(f"      From: {msg.get('from_parent')}")
            print(f"      Message: {msg.get('message')}")
            print(f"      Bonus: {msg.get('bonus_minutes')} minutes")
        else:
            print("\n   ❌ No messages found!")
    else:
        print(f"   ❌ Failed to fetch messages: {response.json()}")
    
    print("\n" + "="*60)
    print("✓ MESSAGING SYSTEM TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        test_messaging_system()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
