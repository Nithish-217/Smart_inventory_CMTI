import requests
import json

print("=" * 60)
print("OFFICER DASHBOARD API TEST")
print("=" * 60)

# Login to get session
print("\n1. Logging in as OF01...")
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'OF01',
    'password': 'password'
})
print(f"   Login Status: {login_response.status_code}")
if login_response.status_code == 200:
    login_data = login_response.json()
    session_id = login_data.get('session_id')
    print(f"   ✓ Got session_id: {session_id}")
    
    headers = {'x-session-id': session_id}
    
    # Test 2: Get profile
    print("\n2. Testing /api/auth/profile...")
    profile_res = requests.get('http://localhost:8000/api/auth/profile', headers=headers)
    print(f"   Status: {profile_res.status_code}")
    if profile_res.ok:
        profile = profile_res.json()
        print(f"   ✓ Profile: {profile}")
    else:
        print(f"   ✗ Error: {profile_res.text}")
    
    # Test 3: Get officer tools
    print("\n3. Testing /api/officer/tools...")
    tools_res = requests.get('http://localhost:8000/api/officer/tools', headers=headers)
    print(f"   Status: {tools_res.status_code}")
    if tools_res.ok:
        tools = tools_res.json()
        print(f"   ✓ Got {len(tools)} tools")
        if len(tools) > 0:
            print(f"   Sample tool: {tools[0]}")
    else:
        print(f"   ✗ Error: {tools_res.text}")
    
    # Test 4: Get officer tool issues
    print("\n4. Testing /api/officer/tool-issues...")
    issues_res = requests.get('http://localhost:8000/api/officer/tool-issues', headers=headers)
    print(f"   Status: {issues_res.status_code}")
    if issues_res.ok:
        issues = issues_res.json()
        print(f"   ✓ Got {len(issues)} issues")
        if len(issues) > 0:
            print(f"   Sample issue: {issues[0]}")
    else:
        print(f"   ✗ Error: {issues_res.text}")
    
    # Test 5: Calculate dashboard stats
    print("\n5. Calculating dashboard stats...")
    if tools_res.ok and issues_res.ok:
        tools = tools_res.json()
        issues = issues_res.json()
        total = len(tools) if isinstance(tools, list) else 0
        available = len([t for t in tools if (t.get('quantity', 0) > 0)]) if isinstance(tools, list) else 0
        issue_count = len(issues) if isinstance(issues, list) else 0
        print(f"   Total Tools: {total}")
        print(f"   Available Tools: {available}")
        print(f"   Under Maintenance: {issue_count}")
    
else:
    print(f"   ✗ Login failed: {login_response.text}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
