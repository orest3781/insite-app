"""
Database Cleanup Script
Fixes orphaned records and foreign key constraint violations.
"""
import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import Database
from src.core.config import ConfigManager

def cleanup_orphaned_records():
    """Clean up orphaned records in the database."""
    print("\n" + "="*80)
    print("  DATABASE CLEANUP - Fixing Foreign Key Violations")
    print("="*80 + "\n")
    
    portable_root = Path(__file__).parent
    config = ConfigManager(portable_root)
    db_path = config.get('database_path') or str(portable_root / 'data' / 'previewless.db')
    
    db = Database(db_path)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check current foreign key errors
        cursor.execute("PRAGMA foreign_key_check")
        errors_before = len(cursor.fetchall())
        print(f"Foreign key errors before cleanup: {errors_before}")
        
        if errors_before == 0:
            print("✅ No cleanup needed!")
            return
        
        print("\nCleaning up orphaned records...\n")
        
        # Clean up classifications without parent files
        cursor.execute("""
            SELECT COUNT(*) FROM classifications 
            WHERE file_id NOT IN (SELECT file_id FROM files WHERE file_id IS NOT NULL)
        """)
        orphaned_classifications = cursor.fetchone()[0]
        
        if orphaned_classifications > 0:
            cursor.execute("""
                DELETE FROM classifications 
                WHERE file_id NOT IN (SELECT file_id FROM files WHERE file_id IS NOT NULL)
            """)
            print(f"✅ Deleted {orphaned_classifications} orphaned classification records")
        
        # Clean up descriptions without parent files  
        cursor.execute("""
            SELECT COUNT(*) FROM descriptions
            WHERE file_id NOT IN (SELECT file_id FROM files WHERE file_id IS NOT NULL)
        """)
        orphaned_descriptions = cursor.fetchone()[0]
        
        if orphaned_descriptions > 0:
            cursor.execute("""
                DELETE FROM descriptions
                WHERE file_id NOT IN (SELECT file_id FROM files WHERE file_id IS NOT NULL)
            """)
            print(f"✅ Deleted {orphaned_descriptions} orphaned description records")
        
        # Clean up pages without parent files
        cursor.execute("""
            SELECT COUNT(*) FROM pages
            WHERE file_id NOT IN (SELECT file_id FROM files WHERE file_id IS NOT NULL)
        """)
        orphaned_pages = cursor.fetchone()[0]
        
        if orphaned_pages > 0:
            cursor.execute("""
                DELETE FROM pages
                WHERE file_id NOT IN (SELECT file_id FROM files WHERE file_id IS NOT NULL)
            """)
            print(f"✅ Deleted {orphaned_pages} orphaned page records")
        
        # Check foreign key errors after cleanup
        cursor.execute("PRAGMA foreign_key_check")
        errors_after = len(cursor.fetchall())
        
        print(f"\nForeign key errors after cleanup: {errors_after}")
        
        if errors_after == 0:
            print("\n✅ All foreign key violations fixed!")
        else:
            print(f"\n⚠️  {errors_after} foreign key errors remain (may require manual intervention)")
        
        # Show final statistics
        print("\n" + "="*80)
        print("  Database Statistics After Cleanup")
        print("="*80)
        
        tables = ['files', 'pages', 'classifications', 'descriptions', 'tags']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    cleanup_orphaned_records()
