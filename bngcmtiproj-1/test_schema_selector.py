import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.schema_selector import SchemaSelector

print("=" * 60)
print("SCHEMA SELECTOR TEST")
print("=" * 60)

# Test 1: Initialize schema selector
print("\n1. Initializing SchemaSelector...")
try:
    selector = SchemaSelector()
    print(f"   ✓ SchemaSelector initialized")
    print(f"   Found {len(selector.schema)} tables in schema:")
    for table_name in selector.schema.keys():
        print(f"   - {table_name}")
except Exception as e:
    print(f"   ✗ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Test with a sample question
print("\n2. Testing schema selection for question: 'How many hammers do we have?'")
try:
    question = "How many hammers do we have?"
    relevant_schema = selector.get_relevant_schema(question)
    print(f"   Selected {len(relevant_schema)} tables:")
    for table_name, columns in relevant_schema.items():
        print(f"   - {table_name}: {columns}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test with another question
print("\n3. Testing schema selection for question: 'Show me all tool requests'")
try:
    question = "Show me all tool requests"
    relevant_schema = selector.get_relevant_schema(question)
    print(f"   Selected {len(relevant_schema)} tables:")
    for table_name, columns in relevant_schema.items():
        print(f"   - {table_name}: {columns}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Format schema for prompt
print("\n4. Testing schema formatting for prompt...")
try:
    question = "How many tools are available?"
    relevant_schema = selector.get_relevant_schema(question)
    formatted = selector.format_schema_for_prompt(relevant_schema)
    print(f"   Formatted schema:")
    print(formatted)
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
