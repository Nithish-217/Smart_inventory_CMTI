import requests
import json

print("=" * 60)
print("AI QUERY ENDPOINT TEST")
print("=" * 60)

# Login to get session
print("\n1. Logging in...")
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'OF01',
    'password': 'password'
})
print(f"   Login Status: {login_response.status_code}")
print(f"   Response: {login_response.text}")
if login_response.status_code == 200:
    login_data = login_response.json()
    session_id = login_data.get('session_id')
    print(f"   ✓ Got session_id: {session_id}")
    
    # Test AI query
    print("\n2. Testing AI query: 'How many hammers do we have?'")
    headers = {'x-session-id': session_id}
    ai_response = requests.post(
        'http://localhost:8000/api/officer/ai-query',
        headers=headers,
        json={'query': 'How many hammers do we have?'}
    )
    print(f"   Status: {ai_response.status_code}")
    if ai_response.status_code == 200:
        result = ai_response.json()
        print(f"   ✓ AI Query successful")
        print(f"   SQL: {result.get('sql', 'N/A')}")
        print(f"   Answer: {result.get('answer', 'N/A')}")
    else:
        print(f"   Response: {ai_response.text[:500]}")
else:
    print(f"   Login failed: {login_response.text}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
