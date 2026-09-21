import requests
import json

print("=" * 60)
print("OFFICER ENDPOINT TEST")
print("=" * 60)

# Test 1: Test officer/tools endpoint without auth (should fail)
print("\n1. Testing /api/officer/tools without session...")
try:
    response = requests.get('http://localhost:8000/api/officer/tools')
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✓ Expected: Unauthorized (no session)")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 2: Test officer/tools endpoint with a session (need to login first)
print("\n2. Testing login to get session...")
try:
    login_response = requests.post('http://localhost:8000/api/auth/login', json={
        'username': 'OF02',
        'password': 'password'
    })
    print(f"   Login Status: {login_response.status_code}")
    if login_response.status_code == 200:
        login_data = login_response.json()
        session_id = login_data.get('session_id')
        print(f"   ✓ Got session_id: {session_id}")
        
        # Test 3: Now test officer/tools with session
        print("\n3. Testing /api/officer/tools with session...")
        headers = {'x-session-id': session_id}
        tools_response = requests.get('http://localhost:8000/api/officer/tools', headers=headers)
        print(f"   Status: {tools_response.status_code}")
        if tools_response.status_code == 200:
            tools = tools_response.json()
            print(f"   ✓ Got {len(tools)} tools")
            if len(tools) > 0:
                print(f"   Sample tool: {tools[0]}")
        else:
            print(f"   Response: {tools_response.text[:200]}")
    else:
        print(f"   Login failed: {login_response.text}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
