import sqlite3
import os
from datetime import datetime

class MemoryDatabase:
    def __init__(self, db_path="smart_glasses.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Creates a database connection with dictionary row access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates the initial tables if they do not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Memories table: stores general context, timestamps, and image links
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image_path TEXT,
                    tag TEXT
                )
            """)
            
            # Objects table: tracks specific items, locations, and confidence
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE,
                    location TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    image_path TEXT
                )
            """)
            conn.commit()

    def record_memory(self, description: str, image_path: str = None, tag: str = "general") -> int:
        """Stores a general observation or event."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (timestamp, description, image_path, tag)
                VALUES (?, ?, ?, ?)
            """, (now, description, image_path, tag))
            conn.commit()
            return cursor.lastrowid

    def update_object_location(self, object_name: str, location: str, image_path: str = None) -> None:
        """Updates where an object was last seen, or inserts it if new."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if object already exists
            cursor.execute("SELECT id FROM objects WHERE name = ?", (object_name,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute("""
                    UPDATE objects
                    SET location = ?, last_seen = ?, image_path = ?
                    WHERE id = ?
                """, (location, now, image_path, row["id"]))
            else:
                cursor.execute("""
                    INSERT INTO objects (name, location, last_seen, image_path)
                    VALUES (?, ?, ?, ?)
                """, (object_name, location, now, image_path))
            conn.commit()

    def find_object(self, object_name: str):
        """Finds the last known location and timestamp of a given object."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, location, last_seen, image_path
                FROM objects
                WHERE name LIKE ?
                ORDER BY last_seen DESC
                LIMIT 1
            """, (f"%{object_name}%",))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_recent_memories(self, limit: int = 5):
        """Retrieves the latest recorded memories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, description, image_path, tag
                FROM memories
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]