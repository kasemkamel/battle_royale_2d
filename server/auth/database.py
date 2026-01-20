# server\auth\database.py
"""
Database Manager
Handles SQLite database operations for user accounts and persistence.
"""

import sqlite3
import json
from typing import Optional
from server.models.user import User


class Database:
    """SQLite database manager for user accounts."""
    
    def __init__(self, db_path: str = "game_data.db"):
        self.db_path = db_path
        self.connection = None
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist."""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.connection.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                email TEXT,
                stats TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
        print(f"[Database] Initialized at {self.db_path}")
    
    def create_user(self, username: str, password: str, email: str = "") -> Optional[User]:
        """
        Create a new user account.
        Returns User object if successful, None if username exists.
        """
        cursor = self.connection.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return None
        
        # Hash password
        password_hash, salt = User.hash_password(password)
        
        # Default stats
        stats = json.dumps({
            "matches_played": 0,
            "wins": 0,
            "kills": 0,
            "deaths": 0,
            "total_damage": 0,
            "total_playtime": 0
        })
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, email, stats)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, salt, email, stats))
        
        self.connection.commit()
        user_id = cursor.lastrowid
        
        return User(user_id, username, password_hash, salt, email, json.loads(stats))
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT user_id, username, password_hash, salt, email, stats
            FROM users WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return User(
            user_id=row[0],
            username=row[1],
            password_hash=row[2],
            salt=row[3],
            email=row[4],
            stats=json.loads(row[5]) if row[5] else {}
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT user_id, username, password_hash, salt, email, stats
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return User(
            user_id=row[0],
            username=row[1],
            password_hash=row[2],
            salt=row[3],
            email=row[4],
            stats=json.loads(row[5]) if row[5] else {}
        )
    
    def update_user_stats(self, user_id: int, stats: dict):
        """Update user statistics."""
        cursor = self.connection.cursor()
        cursor.execute('''
            UPDATE users SET stats = ? WHERE user_id = ?
        ''', (json.dumps(stats), user_id))
        self.connection.commit()
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("[Database] Connection closed")