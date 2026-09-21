import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, select, text, inspect
from app.core.config import settings

print("=" * 60)
print("DATABASE CONNECTION TEST")
print("=" * 60)

# Test 1: Database connection
print("\n1. Testing database connection...")
try:
    engine = create_engine(settings.db_url(), pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"   ✓ Database connected successfully")
        print(f"   Database URL: {settings.db_url()}")
except Exception as e:
    print(f"   ✗ Database connection failed: {e}")
    sys.exit(1)

# Test 2: List all tables
print("\n2. Listing all tables in database...")
try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   Found {len(tables)} tables:")
    for table in tables:
        print(f"   - {table}")
except Exception as e:
    print(f"   ✗ Failed to list tables: {e}")

# Test 3: Check tool_inventory table structure
print("\n3. Checking tool_inventory table structure...")
try:
    columns = inspector.get_columns('tool_inventory')
    print(f"   Columns in tool_inventory:")
    for col in columns:
        print(f"   - {col['name']} ({col['type']})")
except Exception as e:
    print(f"   ✗ Failed to get columns: {e}")

# Test 4: Query tool_inventory data
print("\n4. Querying tool_inventory data...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, tool_name, quantity, range_mm, identification_code, make FROM tool_inventory ORDER BY tool_name"))
        tools = result.fetchall()
        print(f"   Found {len(tools)} tools in inventory:")
        
        if len(tools) == 0:
            print("   ⚠ WARNING: No tools found in database!")
        else:
            for tool in tools[:10]:  # Show first 10
                print(f"   - ID: {tool[0]}, Name: {tool[1]}, Quantity: {tool[2]}")
            if len(tools) > 10:
                print(f"   ... and {len(tools) - 10} more tools")
except Exception as e:
    print(f"   ✗ Failed to query tools: {e}")

# Test 5: Check users table
print("\n5. Checking users table...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, username, full_name, role, is_first_login, is_active FROM users"))
        users = result.fetchall()
        print(f"   Found {len(users)} users:")
        for user in users:
            print(f"   - ID: {user[0]}, Username: {user[1]}, Name: {user[2]}, Role: {user[3]}, First Login: {user[4]}, Active: {user[5]}")
except Exception as e:
    print(f"   ✗ Failed to query users: {e}")

# Test 6: Check role locks
print("\n6. Checking role locks...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, role, session_id, locked_at FROM role_locks"))
        locks = result.fetchall()
        print(f"   Found {len(locks)} role locks:")
        for lock in locks:
            print(f"   - ID: {lock[0]}, Role: {lock[1]}, Session: {lock[2]}, Locked At: {lock[3]}")
        
        # Clear all role locks
        if len(locks) > 0:
            print("\n7. Clearing role locks...")
            conn.execute(text("DELETE FROM role_locks"))
            conn.commit()
            print("   ✓ All role locks cleared")
        
        # Reset first login for officers
        print("\n8. Resetting first login for officers...")
        conn.execute(text("UPDATE users SET is_first_login = false WHERE role = 'OFFICER'"))
        conn.commit()
        print("   ✓ First login reset for officers")
        
        # Reset password for OF02 to default
        print("\n9. Resetting password for OF02 to default...")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("password")
        conn.execute(text("UPDATE users SET hashed_password = :pwd WHERE username = 'OF02'"), {"pwd": hashed_password})
        conn.commit()
        print("   ✓ Password reset for OF02")
        
        # Clear sessions
        print("\n10. Clearing all sessions...")
        conn.execute(text("DELETE FROM sessions"))
        conn.commit()
        print("   ✓ All sessions cleared")
        
        # Activate OF02
        print("\n11. Activating OF02...")
        conn.execute(text("UPDATE users SET is_active = true WHERE username = 'OF02'"))
        conn.commit()
        print("   ✓ OF02 activated")
        
        # Reset password for OF01 to default
        print("\n12. Resetting password for OF01 to default...")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("password")
        conn.execute(text("UPDATE users SET hashed_password = :pwd WHERE username = 'OF01'"), {"pwd": hashed_password})
        conn.commit()
        print("   ✓ Password reset for OF01")
except Exception as e:
    print(f"   ✗ Failed to query role locks: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
