# client/core/game_state.py
"""
Game State
Maintains global client-side game state.
"""

from shared.enums import GameState


class ClientGameState:
    """Global client game state manager."""
    
    def __init__(self):
        # Connection state
        self.is_connected = False
        
        # User data
        self.user_id = None
        self.username = None
        self.stats = {}
        
        # Player data
        self.player_id = None
        
        # Current game state
        self.state = GameState.MENU
        
        # Settings
        self.settings = {
            "music_volume": 0.5,
            "sfx_volume": 0.7,
            "fullscreen": False
        }
    
    def login(self, user_id: int, username: str, stats: dict):
        """Handle successful login."""
        self.user_id = user_id
        self.username = username
        self.stats = stats
        print(f"[GameState] Logged in as {username} (ID: {user_id})")
    
    def logout(self):
        """Handle logout."""
        print(f"[GameState] Logged out user {self.username}")
        self.user_id = None
        self.username = None
        self.player_id = None
        self.stats = {}
    
    def set_player_id(self, player_id: int):
        """Set the current player ID."""
        self.player_id = player_id
        print(f"[GameState] Player ID set to {player_id}")
    
    def set_connected(self, connected: bool):
        """Set connection status."""
        self.is_connected = connected
        if not connected:
            print("[GameState] Disconnected from server")
    
    def get_state_dict(self) -> dict:
        """Get state as dictionary."""
        return {
            "is_connected": self.is_connected,
            "user_id": self.user_id,
            "username": self.username,
            "stats": self.stats,
            "player_id": self.player_id,
            "state": self.state.name
        }
    
    def __repr__(self):
        return f"GameState(user={self.username}, connected={self.is_connected})"