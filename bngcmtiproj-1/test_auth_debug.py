import requests
import json

print("=" * 60)
print("AUTHENTICATION DEBUG TEST")
print("=" * 60)

# Test 1: Login
print("\n1. Testing login...")
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'OF01',
    'password': 'password'
})
print(f"   Login Status: {login_response.status_code}")
if login_response.status_code == 200:
    login_data = login_response.json()
    print(f"   Response: {json.dumps(login_data, indent=2)}")
    session_id = login_data.get('session_id')
    print(f"   ✓ Session ID: {session_id}")
    
    # Test 2: Check what header is expected
    print("\n2. Testing /api/officer/tools with x-session-id header...")
    headers = {'x-session-id': session_id}
    tools_res = requests.get('http://localhost:8000/api/officer/tools', headers=headers)
    print(f"   Status: {tools_res.status_code}")
    print(f"   Response: {tools_res.text[:200]}")
    
    # Test 3: Try with Authorization header
    print("\n3. Testing /api/officer/tools with Authorization header...")
    headers_auth = {'Authorization': f'Bearer {session_id}'}
    tools_res_auth = requests.get('http://localhost:8000/api/officer/tools', headers=headers_auth)
    print(f"   Status: {tools_res_auth.status_code}")
    print(f"   Response: {tools_res_auth.text[:200]}")
    
    # Test 4: Check session-check endpoint
    print("\n4. Testing /api/auth/session-check...")
    session_check = requests.get('http://localhost:8000/api/auth/session-check', headers={'x-session-id': session_id})
    print(f"   Status: {session_check.status_code}")
    print(f"   Response: {json.dumps(session_check.json(), indent=2)}")
    
else:
    print(f"   ✗ Login failed: {login_response.text}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
