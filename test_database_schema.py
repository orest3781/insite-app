"""
Test script to check if the database class has the get_schema_version method.
"""
from src.models.database import Database

# Create test database
db = Database(":memory:")  # SQLite in-memory database for testing
print(f"SCHEMA_VERSION: {db.SCHEMA_VERSION}")

# Check if get_schema_version method exists and works
try:
    schema_version = db.get_schema_version()
    print(f"get_schema_version() returned: {schema_version}")
    print("✅ SUCCESS: get_schema_version() method is working!")
except AttributeError as e:
    print(f"❌ ERROR: {e}")
    print("The get_schema_version method is missing or not properly defined.")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")