#!/usr/bin/env python3
"""
Initialize the database with required schema.
"""
from pathlib import Path
from src.models.database import Database
from src.core.config import ConfigManager

def main():
    print("Initializing database...")
    
    # Get database path from config
    portable_root = Path(__file__).parent
    config = ConfigManager(portable_root)
    db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
    
    # Initialize database
    db = Database(db_path)
    db.initialize()
    
    print(f"✅ Database initialized successfully at: {db_path}")
    print("\nYou can now run the app with: python main.py")

if __name__ == "__main__":
    main()
