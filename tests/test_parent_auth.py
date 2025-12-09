#!/usr/bin/env python3
"""
Stub for moved test. Original test files have been moved to `tests/` for a cleaner project layout.

Run the test from the `tests` directory, e.g.:

    python -m tests.test_parent_auth

This file remains as a lightweight notice to developers.
"""

print("This test has moved to ./tests/test_parent_auth.py")
print("Run it from the project root with: python -m tests.test_parent_auth")
#!/usr/bin/env python3
"""
Test script to debug parent authorization issue
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log(msg, level="info"):
    prefix = {
        "info": f"{Colors.OKBLUE}[INFO]{Colors.ENDC}",
        "success": f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC}",
        "error": f"{Colors.FAIL}[ERROR]{Colors.ENDC}",
        "debug": f"{Colors.OKCYAN}[DEBUG]{Colors.ENDC}",
    }.get(level, "[LOG]")
    print(f"{prefix} {msg}")


def test_parent_workflow():
    """Test the complete parent workflow"""
    session = requests.Session()
    
    # Unique test credentials using timestamp
    timestamp = datetime.now().strftime("%H%M%S%f")
    parent_email = f"parent_test_{timestamp}@test.com"
    parent_password = "TestPassword123!"
    parent_name = f"Test Parent {timestamp}"
    
    child_email = f"child_test_{timestamp}@test.com"
    child_password = "ChildPassword123!"
    child_name = f"Test Child {timestamp}"
    
    log(f"Testing with timestamp: {timestamp}", "debug")
    
    # Step 1: Register as parent
    log("Step 1: Registering parent account...", "info")
    register_data = {
        'email': parent_email,
        'password': parent_password,
        'confirm_password': parent_password,
        'name': parent_name,
        'is_parent': 'on'
    }
    
    resp = session.post(f"{BASE_URL}/register", data=register_data)
    log(f"  Register response: {resp.status_code}", "debug")
    if resp.status_code != 302:  # Redirect after successful registration
        log(f"  Registration failed: {resp.text[:200]}", "error")
        return
    log("  ✓ Parent registered successfully", "success")
    
    # Step 2: Login as parent
    log("Step 2: Logging in as parent...", "info")
    login_data = {
        'email': parent_email,
        'password': parent_password
    }
    
    resp = session.post(f"{BASE_URL}/login", data=login_data)
    log(f"  Login response: {resp.status_code}", "debug")
    if resp.status_code != 302:  # Redirect after successful login
        log(f"  Login failed: {resp.text[:200]}", "error")
        return
    log("  ✓ Parent logged in successfully", "success")
    
    # Check session cookies
    log(f"  Session cookies: {session.cookies.get_dict()}", "debug")
    
    # Step 3: Verify we're on parent dashboard
    log("Step 3: Verifying parent dashboard access...", "info")
    resp = session.get(f"{BASE_URL}/parent-dashboard")
    log(f"  Dashboard response: {resp.status_code}", "debug")
    if resp.status_code == 200:
        log("  ✓ Parent dashboard accessible", "success")
    else:
        log(f"  ✗ Cannot access parent dashboard: {resp.status_code}", "error")
        return
    
    # Step 4: Attempt to add child via API
    log("Step 4: Attempting to add child via API...", "info")
    api_data = {
        'child_name': child_name,
        'child_email': child_email,
        'child_password': child_password
    }
    
    log(f"  Request data: {json.dumps(api_data, indent=2)}", "debug")
    log(f"  Session cookies before API call: {session.cookies.get_dict()}", "debug")
    
    resp = session.post(
        f"{BASE_URL}/api/add-child",
        json=api_data,
        headers={'Content-Type': 'application/json'}
    )
    
    log(f"  API response status: {resp.status_code}", "debug")
    log(f"  API response body: {resp.text}", "debug")
    
    if resp.status_code == 201:
        log("  ✓ Child added successfully!", "success")
        result = resp.json()
        log(f"  Child ID: {result.get('child_id')}", "success")
    else:
        log(f"  ✗ Failed to add child: {resp.status_code}", "error")
        log(f"  Error: {resp.json()}", "error")

if __name__ == "__main__":
    log("=" * 60, "info")
    log("PARENT AUTHORIZATION TEST", "info")
    log("=" * 60, "info")
    test_parent_workflow()
    log("=" * 60, "info")
    log("Test complete. Check Flask logs above for debug output.", "info")
