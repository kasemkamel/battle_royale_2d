# server\auth\authenticator.py
"""
Authenticator
Handles user authentication, registration, and session management.
"""

from typing import Optional, Dict
from server.auth.database import Database
from server.models.user import User


class Authenticator:
    """Manages user authentication and sessions."""
    
    def __init__(self, database: Database):
        self.database = database
        self.active_sessions: Dict[int, User] = {}  # user_id -> User
    
    def register(self, username: str, password: str, email: str = "") -> tuple:
        """
        Register a new user.
        Returns (success: bool, message: str, user: User or None)
        """
        # Validate input
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters", None
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        # Attempt to create user
        user = self.database.create_user(username, password, email)
        
        if user is None:
            return False, "Username already exists", None
        
        print(f"[Auth] New user registered: {username}")
        return True, "Registration successful", user
    
    def login(self, username: str, password: str) -> tuple:
        """
        Authenticate user login.
        Returns (success: bool, message: str, user: User or None)
        """
        # Retrieve user
        user = self.database.get_user_by_username(username)
        
        if user is None:
            return False, "Invalid username or password", None
        
        # Verify password
        if not user.verify_password(password):
            return False, "Invalid username or password", None
        
        # Create session
        self.active_sessions[user.user_id] = user
        
        print(f"[Auth] User logged in: {username}")
        return True, "Login successful", user
    
    def logout(self, user_id: int):
        """Logout user and remove session."""
        if user_id in self.active_sessions:
            user = self.active_sessions[user_id]
            del self.active_sessions[user_id]
            print(f"[Auth] User logged out: {user.username}")
    
    def get_session(self, user_id: int) -> Optional[User]:
        """Get active user session."""
        return self.active_sessions.get(user_id)
    
    def is_authenticated(self, user_id: int) -> bool:
        """Check if user has active session."""
        return user_id in self.active_sessions
    
    def update_user_stats(self, user_id: int, **kwargs):
        """Update user statistics."""
        user = self.active_sessions.get(user_id)
        if user:
            user.update_stats(**kwargs)
            self.database.update_user_stats(user_id, user.stats)