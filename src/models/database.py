"""
Database module for Previewless Insight Viewer.

This module handles all database operations including schema creation,
migrations, and CRUD operations for images, analyses, projects, and sessions.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager with FTS5 full-text search support.
    
    Manages persistent storage for:
    - Images and their metadata
    - OCR text extraction results
    - LLM analysis results
    - Projects and sessions
    - Search history and preferences
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Absolute path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        
        logger.info(f"Database initialized: {self.db_path}")
        
    def get_schema_version(self) -> int:
        """
        Get the current schema version of the database.
        
        Returns:
            int: The current schema version
        """
        return self.SCHEMA_VERSION
        
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Active database connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            conn.close()
    
    def initialize(self):
        """
        Initialize database schema and FTS5 indexes.
        Creates all tables if they don't exist.
        """
        logger.info("Initializing database schema...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable foreign key support
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create P1 schema tables
            self._create_files_table(cursor)
            self._create_pages_table(cursor)
            self._create_classifications_table(cursor)
            self._create_descriptions_table(cursor)
            
            # Create FTS5 virtual tables for full-text search
            self._create_fts_tables(cursor)
            
            # Create indexes for performance
            self._create_indexes(cursor)
        
        logger.info("Database schema initialized successfully")
    
    def _create_files_table(self, cursor: sqlite3.Cursor):
        """Create files table for P1 schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                file_type TEXT,
                page_count INTEGER,
                file_size INTEGER,
                created_at TEXT,
                modified_at TEXT,
                analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.debug("Files table created")
    
    def _create_pages_table(self, cursor: sqlite3.Cursor):
        """Create pages table for P1 schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                page_id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                ocr_text TEXT,
                ocr_confidence REAL,
                ocr_mode TEXT,
                FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
            )
        """)
        logger.debug("Pages table created")
    
    def _create_classifications_table(self, cursor: sqlite3.Cursor):
        """Create classifications table for P1 schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                classification_id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                tag_number INTEGER,
                tag_text TEXT,
                confidence REAL,
                model_used TEXT,
                FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
            )
        """)
        logger.debug("Classifications table created")
    
    def _create_descriptions_table(self, cursor: sqlite3.Cursor):
        """Create descriptions table for P1 schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS descriptions (
                description_id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                description_text TEXT,
                confidence REAL,
                model_used TEXT,
                FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
            )
        """)
        logger.debug("Descriptions table created")
    
    def _create_fts_tables(self, cursor: sqlite3.Cursor):
        """Create FTS5 virtual tables for full-text search."""
        
        # FTS for pages OCR text
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                ocr_text,
                content='pages',
                content_rowid='page_id'
            )
        """)
        
        # FTS for classifications
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS classifications_fts USING fts5(
                tag_text,
                content='classifications',
                content_rowid='classification_id'
            )
        """)
        
        # Create triggers to keep FTS tables in sync
        
        # Pages FTS triggers
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
                INSERT INTO pages_fts(rowid, ocr_text)
                VALUES (new.page_id, new.ocr_text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
                DELETE FROM pages_fts WHERE rowid = old.page_id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
                DELETE FROM pages_fts WHERE rowid = old.page_id;
                INSERT INTO pages_fts(rowid, ocr_text)
                VALUES (new.page_id, new.ocr_text);
            END
        """)
        
        # Classifications FTS triggers
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS classifications_ai AFTER INSERT ON classifications BEGIN
                INSERT INTO classifications_fts(rowid, tag_text)
                VALUES (new.classification_id, new.tag_text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS classifications_ad AFTER DELETE ON classifications BEGIN
                DELETE FROM classifications_fts WHERE rowid = old.classification_id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS classifications_au AFTER UPDATE ON classifications BEGIN
                DELETE FROM classifications_fts WHERE rowid = old.classification_id;
                INSERT INTO classifications_fts(rowid, tag_text)
                VALUES (new.classification_id, new.tag_text);
            END
        """)
        
        logger.debug("FTS5 tables and triggers created")
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Create indexes for improved query performance."""
        
        indexes = [
            # Files indexes
            "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)",
            "CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)",
            "CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)",
            
            # Pages indexes
            "CREATE INDEX IF NOT EXISTS idx_pages_file ON pages(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_pages_number ON pages(page_number)",
            
            # Classifications indexes
            "CREATE INDEX IF NOT EXISTS idx_classifications_file ON classifications(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_classifications_tag ON classifications(tag_text)",
            
            # Descriptions indexes
            "CREATE INDEX IF NOT EXISTS idx_descriptions_file ON descriptions(file_id)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        logger.debug(f"Created {len(indexes)} indexes")
    
    def search_full_text(self, query: str, search_type: str = 'both', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Perform full-text search across OCR and/or classification content.
        
        Args:
            query: Search query (FTS5 syntax supported)
            search_type: 'ocr', 'classifications', or 'both'
            limit: Maximum number of results
            
        Returns:
            List of matching records with file information
        """
        results = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if search_type in ('ocr', 'both'):
                cursor.execute("""
                    SELECT 
                        f.file_id,
                        f.file_path,
                        f.file_type,
                        p.ocr_text,
                        p.ocr_confidence,
                        'ocr' as result_type,
                        rank
                    FROM pages_fts
                    JOIN pages p ON pages_fts.rowid = p.page_id
                    JOIN files f ON p.file_id = f.file_id
                    WHERE pages_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
                
                results.extend([dict(row) for row in cursor.fetchall()])
            
            if search_type in ('classifications', 'both'):
                cursor.execute("""
                    SELECT 
                        f.file_id,
                        f.file_path,
                        f.file_type,
                        c.tag_text,
                        c.confidence,
                        c.model_used,
                        'classification' as result_type,
                        rank
                    FROM classifications_fts
                    JOIN classifications c ON classifications_fts.rowid = c.classification_id
                    JOIN files f ON c.file_id = f.file_id
                    WHERE classifications_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
                
                results.extend([dict(row) for row in cursor.fetchall()])
        
        # Sort combined results by rank
        results.sort(key=lambda x: x.get('rank', 0))
        
        return results[:limit]
    
    def vacuum(self):
        """Optimize database by rebuilding and compacting."""
        logger.info("Running VACUUM on database...")
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database optimized")
    
    def get_analyzed_files(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all analyzed files with their classifications and descriptions.
        
        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip (for pagination)
            
        Returns:
            List of file records with aggregated tags and descriptions
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get files with their descriptions and aggregated tags
            cursor.execute("""
                SELECT 
                    f.file_id,
                    f.file_path,
                    f.file_type,
                    f.page_count,
                    f.file_size,
                    f.analyzed_at,
                    d.description_text,
                    d.confidence as description_confidence,
                    GROUP_CONCAT(c.tag_text, ', ') as tags,
                    AVG(c.confidence) as avg_tag_confidence
                FROM files f
                LEFT JOIN descriptions d ON f.file_id = d.file_id
                LEFT JOIN classifications c ON f.file_id = c.file_id
                GROUP BY f.file_id
                ORDER BY f.analyzed_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_file_details(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific file.
        
        Args:
            file_id: Database ID of the file
            
        Returns:
            Dictionary with complete file information including pages, tags, and description
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get file metadata
            cursor.execute("""
                SELECT * FROM files WHERE file_id = ?
            """, (file_id,))
            
            file_data = cursor.fetchone()
            if not file_data:
                return None
            
            result = dict(file_data)
            
            # Get pages with OCR results
            cursor.execute("""
                SELECT * FROM pages WHERE file_id = ? ORDER BY page_number
            """, (file_id,))
            result['pages'] = [dict(row) for row in cursor.fetchall()]
            
            # Get classifications
            cursor.execute("""
                SELECT * FROM classifications WHERE file_id = ? ORDER BY confidence DESC
            """, (file_id,))
            result['classifications'] = [dict(row) for row in cursor.fetchall()]
            
            # Get description
            cursor.execute("""
                SELECT * FROM descriptions WHERE file_id = ?
            """, (file_id,))
            desc = cursor.fetchone()
            result['description'] = dict(desc) if desc else None
            
            return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts and metrics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['files', 'pages', 'classifications', 'descriptions']
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    stats[f"{table}_count"] = 0
            
            # Database file size
            stats['db_size_bytes'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
            
            return stats
    
    def clear_all_results(self) -> int:
        """
        Clear all analyzed results from the database.
        
        Deletes all records from files table. Related records in pages,
        classifications, and descriptions tables are automatically deleted
        via CASCADE DELETE constraints.
        
        Returns:
            Number of files deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get count before deletion
            cursor.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            
            # Delete all files (cascade will handle related tables)
            cursor.execute("DELETE FROM files")
            
            logger.info(f"Cleared {count} analyzed files from database")
            return count


# Convenience function for getting database instance
def get_database(db_path: str) -> Database:
    """
    Get database instance and initialize if needed.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Initialized Database instance
    """
    db = Database(db_path)
    
    # Initialize schema if database is new or tables don't exist
    if not db.db_path.exists() or db.db_path.stat().st_size == 0:
        db.initialize()
    else:
        # Check if files table exists (P1 schema marker)
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
                if not cursor.fetchone():
                    # Old schema detected, reinitialize with P1 schema
                    logger.warning("Old database schema detected, reinitializing with P1 schema")
                    db.initialize()
        except Exception as e:
            logger.error(f"Error checking database schema: {e}")
            db.initialize()
    
    return db

