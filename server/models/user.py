# server/models/user.py
"""
User Model (Server)
Represents a user account with credentials and statistics.
"""

import hashlib
import os
from typing import Optional


class User:
    """User account model with authentication and stats."""
    
    def __init__(self, user_id: int, username: str, password_hash: str, 
                 salt: str, email: str = "", stats: dict = None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.email = email
        self.stats = stats or {
            "matches_played": 0,
            "wins": 0,
            "kills": 0,
            "deaths": 0,
            "total_damage": 0,
            "total_playtime": 0
        }
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """
        Hash a password with salt.
        Returns (hash, salt) tuple.
        """
        if salt is None:
            salt = os.urandom(32).hex()
        
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        
        return pwd_hash, salt
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against stored hash."""
        pwd_hash, _ = User.hash_password(password, self.salt)
        return pwd_hash == self.password_hash
    
    def update_stats(self, **kwargs):
        """Update user statistics."""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] += value
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary."""
        data = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "stats": self.stats.copy()
        }
        
        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["salt"] = self.salt
        
        return data
    
    @staticmethod
    def from_dict(data: dict) -> 'User':
        """Create User from dictionary."""
        return User(
            user_id=data["user_id"],
            username=data["username"],
            password_hash=data["password_hash"],
            salt=data["salt"],
            email=data.get("email", ""),
            stats=data.get("stats", {})
        )
    
    def __repr__(self):
        return f"User(id={self.user_id}, username='{self.username}')"