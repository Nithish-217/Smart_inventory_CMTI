import google.generativeai as genai
from app.core.config import settings

print("=" * 60)
print("GEMINI API DIRECT TEST")
print("=" * 60)

print(f"\nAPI Key: {settings.GOOGLE_API_KEY[:20]}...")
print(f"Model: {settings.GOOGLE_MODEL}")

try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel(settings.GOOGLE_MODEL)
    
    print("\n1. Testing simple text generation...")
    response = model.generate_content("Hello, can you say 'test'?")
    print(f"   Response type: {type(response)}")
    print(f"   Response: {response}")
    
    if hasattr(response, 'text'):
        print(f"   Text: {response.text}")
    else:
        print("   No text attribute")
        
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
