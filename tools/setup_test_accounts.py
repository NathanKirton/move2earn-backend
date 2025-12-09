#!/usr/bin/env python
"""
Quick setup script to create linked parent-child accounts for manual testing
"""

from database import UserDB
from datetime import datetime

print("\n" + "="*60)
print("SETTING UP TEST ACCOUNTS")
print("="*60 + "\n")

# Create parent account
print("1️⃣ Creating parent account...")
parent_success, parent_id = UserDB.create_user(
    'parent@test.com',
    'parent123',
    'John Parent',
    is_parent=True
)
print(f"   Email: parent@test.com")
print(f"   Password: parent123")
print(f"   ID: {parent_id}\n")

# Create child via parent API
if parent_success:
    print("2️⃣ Creating child account...")
    child_success, child_id = UserDB.add_child(
        parent_id,
        'child@test.com',
        'child123',
        'Emma Child'
    )
    print(f"   Email: child@test.com")
    print(f"   Password: child123")
    print(f"   ID: {child_id}\n")
    
    if child_success:
        # Grant some bonus time with a message
        print("3️⃣ Granting bonus time with message...")
        UserDB.add_earned_game_time(child_id, 50)
        UserDB.add_parent_message(
            child_id,
            'John Parent',
            'Welcome! You started with 50 minutes of game time. Use it wisely!',
            50
        )
        print("   ✓ Granted 50 minutes")
        print("   ✓ Message sent\n")
        
        # Check the messages
        messages = UserDB.get_parent_messages(child_id)
        print(f"4️⃣ Verifying message...")
        if messages:
            msg = messages[0]
            print(f"   ✓ Message from: {msg.get('from_parent')}")
            print(f"   ✓ Message: {msg.get('message')}")
            print(f"   ✓ Bonus: {msg.get('bonus_minutes')} min")

print("\n" + "="*60)
print("✓ TEST ACCOUNTS READY")
print("="*60)
print("\n🔗 LINKS:")
print("   Parent Dashboard: http://localhost:5000/parent-dashboard")
print("   Child Dashboard: http://localhost:5000/dashboard")
print("\n💡 TIP: Log in with the email and password above to test!")
