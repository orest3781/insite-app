"""
Database Quality Control Test Script
Tests all database functionality and reports issues.
"""
import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import Database
from src.core.config import ConfigManager
# Import database extensions for compatibility
import src.models.database_extensions

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def test_database_connection():
    """Test basic database connection."""
    print_section("1. Database Connection Test")
    
    try:
        portable_root = Path(__file__).parent
        config = ConfigManager(portable_root)
        db_path = config.get('database_path') or str(portable_root / 'data' / 'previewless.db')
        
        db = Database(db_path)
        print(f"✅ Database initialized: {db_path}")
        print(f"✅ Database exists: {db.db_path.exists()}")
        print(f"✅ Schema version: {db.get_schema_version()}")
        
        return db
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_database_schema(db):
    """Test database schema."""
    print_section("2. Database Schema Test")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count} rows")
            
            # Check required tables
            required_tables = ['files', 'pages', 'classifications', 'descriptions', 'tags']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            else:
                print(f"✅ All required tables exist")
                
    except Exception as e:
        print(f"❌ Schema test failed: {e}")

def test_tags_table(db):
    """Test tags table structure and operations."""
    print_section("3. Tags Table Test")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check tags table schema
            cursor.execute("PRAGMA table_info(tags)")
            columns = cursor.fetchall()
            
            print("✅ Tags table schema:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " [NOT NULL]" if col[3] else ""
                print(f"   - {col_name} ({col_type}){not_null}")
            
            # Test insert operation
            from datetime import datetime
            test_tag_name = f"QC_Test_Tag_{datetime.now().strftime('%H%M%S')}"
            
            cursor.execute(
                "INSERT INTO tags (name, color, created_at) VALUES (?, ?, ?)",
                (test_tag_name, "#FF0000", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            tag_id = cursor.lastrowid
            print(f"✅ Test tag created with ID: {tag_id}")
            
            # Test select operation
            cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
            tag = cursor.fetchone()
            if tag:
                print(f"✅ Test tag retrieved: {dict(tag)}")
            else:
                print(f"❌ Failed to retrieve test tag")
            
            # Test update operation
            cursor.execute(
                "UPDATE tags SET color = ? WHERE id = ?",
                ("#00FF00", tag_id)
            )
            print(f"✅ Test tag updated")
            
            # Test delete operation
            cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            print(f"✅ Test tag deleted")
            
    except Exception as e:
        print(f"❌ Tags table test failed: {e}")
        import traceback
        traceback.print_exc()

def test_database_methods(db):
    """Test database compatibility methods."""
    print_section("4. Database Methods Test")
    
    try:
        # Test get_connection
        with db.get_connection() as conn:
            print("✅ get_connection() works")
        
        # Test connection (compatibility)
        if hasattr(db, 'connection'):
            with db.connection() as conn:
                print("✅ connection() works (compatibility)")
        else:
            print("⚠️  connection() method not available")
        
        # Test close (compatibility)
        if hasattr(db, 'close'):
            db.close()
            print("✅ close() works (compatibility)")
        else:
            print("⚠️  close() method not available")
        
        # Test ensure_connection (compatibility)
        if hasattr(db, 'ensure_connection'):
            db.ensure_connection()
            print("✅ ensure_connection() works (compatibility)")
        else:
            print("⚠️  ensure_connection() method not available")
            
    except Exception as e:
        print(f"❌ Database methods test failed: {e}")
        import traceback
        traceback.print_exc()

def test_fts_search(db):
    """Test full-text search functionality."""
    print_section("5. Full-Text Search Test")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if FTS tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'")
            fts_tables = [row[0] for row in cursor.fetchall()]
            
            if fts_tables:
                print(f"✅ Found FTS tables: {', '.join(fts_tables)}")
            else:
                print("⚠️  No FTS tables found")
                
    except Exception as e:
        print(f"❌ FTS search test failed: {e}")

def test_database_integrity(db):
    """Test database integrity."""
    print_section("6. Database Integrity Test")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            if result == "ok":
                print("✅ Database integrity: OK")
            else:
                print(f"⚠️  Database integrity issues: {result}")
                
            # Check foreign keys
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            
            if not fk_errors:
                print("✅ Foreign key constraints: OK")
            else:
                print(f"❌ Foreign key errors found: {len(fk_errors)}")
                for error in fk_errors[:5]:  # Show first 5
                    print(f"   {error}")
                    
    except Exception as e:
        print(f"❌ Integrity test failed: {e}")

def main():
    """Run all database QC tests."""
    print("\n" + "="*80)
    print("  DATABASE QUALITY CONTROL TEST")
    print("="*80)
    
    # Test database connection
    db = test_database_connection()
    
    if db:
        # Run all tests
        test_database_schema(db)
        test_tags_table(db)
        test_database_methods(db)
        test_fts_search(db)
        test_database_integrity(db)
        
        print("\n" + "="*80)
        print("  QC TEST COMPLETE")
        print("="*80 + "\n")
    else:
        print("\n❌ Cannot proceed with tests - database connection failed\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
