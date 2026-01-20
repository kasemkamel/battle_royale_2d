# server/models/player.py
"""
Player Model (Server)
Server-side representation of a connected player in a match.
"""

import time
from shared.enums import PlayerState, CharacterClass
from shared.constants import PLAYER_MAX_HEALTH, PLAYER_SPEED


class Player:
    """Server-side player instance."""
    
    def __init__(self, player_id: int, user_id: int, username: str):
        # Identity
        self.player_id = player_id
        self.user_id = user_id
        self.username = username
        
        # State
        self.state = PlayerState.CONNECTED
        self.character_class = CharacterClass.WARRIOR
        
        # Position and movement
        self.x = 0.0
        self.y = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.rotation = 0.0  # Radians
        
        # Combat
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.is_alive = True
        self.last_damage_time = 0
        self.kills = 0
        self.deaths = 0
        
        # Input
        self.input_x = 0.0
        self.input_y = 0.0
        self.actions = {}  # Dict of action states
        
        # Network
        self.last_update = time.time()
        self.ping = 0
        
        # Ready state (for lobby)
        self.ready = False
    
    def update(self, delta_time: float):
        """Update player state (called every server tick)."""
        if not self.is_alive:
            return
        
        # Update velocity based on input
        self.vel_x = self.input_x * PLAYER_SPEED
        self.vel_y = self.input_y * PLAYER_SPEED
        
        # Update position
        self.x += self.vel_x * delta_time
        self.y += self.vel_y * delta_time
        
        # Update timestamp
        self.last_update = time.time()
    
    def take_damage(self, damage: float, attacker_id: int = None):
        """Apply damage to player."""
        if not self.is_alive:
            return False
        
        self.health -= damage
        self.last_damage_time = time.time()
        
        if self.health <= 0:
            self.health = 0
            self.die()
            return True  # Player died
        
        return False  # Player still alive
    
    def die(self):
        """Handle player death."""
        self.is_alive = False
        self.state = PlayerState.DEAD
        self.deaths += 1
        print(f"[Player] {self.username} died")
    
    def respawn(self, x: float, y: float):
        """Respawn player at position."""
        self.x = x
        self.y = y
        self.health = self.max_health
        self.is_alive = True
        self.state = PlayerState.IN_GAME
        self.vel_x = 0
        self.vel_y = 0
        print(f"[Player] {self.username} respawned")
    
    def set_input(self, input_x: float, input_y: float, actions: dict = None):
        """Update player input from client."""
        self.input_x = max(-1, min(1, input_x))  # Clamp to [-1, 1]
        self.input_y = max(-1, min(1, input_y))
        
        if actions:
            self.actions = actions
    
    def to_dict(self, include_private: bool = False) -> dict:
        """
        Serialize player to dictionary for network transmission.
        include_private: Whether to include data only the player should see.
        """
        data = {
            "player_id": self.player_id,
            "user_id": self.user_id,
            "username": self.username,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "rotation": round(self.rotation, 2),
            "health": self.health,
            "max_health": self.max_health,
            "is_alive": self.is_alive,
            "state": self.state.name,
            "character_class": self.character_class.name
        }
        
        if include_private:
            data.update({
                "kills": self.kills,
                "deaths": self.deaths,
                "ping": self.ping
            })
        
        return data
    
    def __repr__(self):
        return f"Player(id={self.player_id}, name='{self.username}', pos=({self.x:.1f}, {self.y:.1f}))"