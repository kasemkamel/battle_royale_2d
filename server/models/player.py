# server/models/player.py
"""
Player Model (Server)
Server-side representation of a connected player in a match.
"""

import time
import math
from shared.enums import PlayerState, CharacterClass
from shared.constants import (
    PLAYER_MAX_HEALTH, PLAYER_SPEED, PLAYER_MAX_MANA, PLAYER_MANA_REGEN,
    PLAYER_SPRINT_MULTIPLIER, PLAYER_DASH_SPEED, PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN
)


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
        self.rotation = 0.0  # Radians (facing direction)
        
        # Movement modifiers
        self.is_sprinting = False
        self.is_dashing = False
        self.dash_direction_x = 0.0
        self.dash_direction_y = 0.0
        self.dash_end_time = 0.0
        self.dash_cooldown_end = 0.0
        
        # Combat
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.mana = PLAYER_MAX_MANA
        self.max_mana = PLAYER_MAX_MANA
        self.is_alive = True
        self.last_damage_time = 0
        self.kills = 0
        self.deaths = 0
        
        # Skills
        self.skills = []  # List of equipped skills
        self.active_effects = []  # Active buffs/debuffs
        
        # Crowd Control
        self.is_stunned = False
        self.stun_end_time = 0
        self.movement_speed_multiplier = 1.0  # For slows/buffs
        
        # Input
        self.input_x = 0.0
        self.input_y = 0.0
        self.mouse_x = 0.0  # Mouse cursor world position
        self.mouse_y = 0.0
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
        
        # Update rotation to face mouse cursor
        self._update_rotation()
        
        # Check dash state
        if self.is_dashing:
            if time.time() >= self.dash_end_time:
                self.is_dashing = False
            else:
                # Override velocity with dash velocity
                self.vel_x = self.dash_direction_x * PLAYER_DASH_SPEED
                self.vel_y = self.dash_direction_y * PLAYER_DASH_SPEED
                self.x += self.vel_x * delta_time
                self.y += self.vel_y * delta_time
                return  # Skip normal movement during dash
        
        # Check stun
        if self.is_stunned:
            if time.time() >= self.stun_end_time:
                self.is_stunned = False
            else:
                # Cannot move while stunned
                self.vel_x = 0
                self.vel_y = 0
                return
        
        # Calculate speed with modifiers
        base_speed = PLAYER_SPEED
        
        if self.is_sprinting:
            base_speed *= PLAYER_SPRINT_MULTIPLIER
        
        base_speed *= self.movement_speed_multiplier  # Apply slows/buffs
        
        # Update velocity based on input
        self.vel_x = self.input_x * base_speed
        self.vel_y = self.input_y * base_speed
        
        # Update position
        self.x += self.vel_x * delta_time
        self.y += self.vel_y * delta_time
        
        # Regenerate mana
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + PLAYER_MANA_REGEN * delta_time)
        
        # Update timestamp
        self.last_update = time.time()
    
    def _update_rotation(self):
        """Update player rotation to face mouse cursor."""
        dx = self.mouse_x - self.x
        dy = self.mouse_y - self.y
        
        if dx != 0 or dy != 0:
            self.rotation = math.atan2(dy, dx)
    
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
    
    def set_input(self, input_x: float, input_y: float, mouse_x: float = None, 
                  mouse_y: float = None, actions: dict = None):
        """Update player input from client."""
        self.input_x = max(-1, min(1, input_x))  # Clamp to [-1, 1]
        self.input_y = max(-1, min(1, input_y))
        
        if mouse_x is not None:
            self.mouse_x = mouse_x
        if mouse_y is not None:
            self.mouse_y = mouse_y
        
        if actions:
            self.actions = actions
            
            # Handle sprint
            self.is_sprinting = actions.get("sprint", False)
            
            # Handle dash
            if actions.get("dash", False) and self.can_dash():
                self.start_dash()
    
    def can_dash(self) -> bool:
        """Check if player can dash."""
        if self.is_dashing:
            return False
        if time.time() < self.dash_cooldown_end:
            return False
        if self.is_stunned:
            return False
        return True
    
    def start_dash(self):
        """Start dash in direction of mouse cursor."""
        # Calculate dash direction
        dx = self.mouse_x - self.x
        dy = self.mouse_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.dash_direction_x = dx / distance
            self.dash_direction_y = dy / distance
        else:
            # Dash in facing direction if mouse is on player
            self.dash_direction_x = math.cos(self.rotation)
            self.dash_direction_y = math.sin(self.rotation)
        
        self.is_dashing = True
        self.dash_end_time = time.time() + PLAYER_DASH_DURATION
        self.dash_cooldown_end = time.time() + PLAYER_DASH_COOLDOWN
        
        print(f"[Player] {self.username} dashed")
    
    def apply_crowd_control(self, cc_type: str, duration: float, intensity: float = 1.0):
        """Apply crowd control effect."""
        if cc_type == "STUN":
            self.is_stunned = True
            self.stun_end_time = time.time() + duration
        elif cc_type == "SLOW":
            self.movement_speed_multiplier = 1.0 - intensity  # intensity = 0.5 means 50% slow
            # TODO: Add timer to remove slow
    
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
            "mana": round(self.mana, 1),
            "max_mana": self.max_mana,
            "is_alive": self.is_alive,
            "state": self.state.name,
            "character_class": self.character_class.name,
            "is_sprinting": self.is_sprinting,
            "is_dashing": self.is_dashing,
            "is_stunned": self.is_stunned
        }
        
        if include_private:
            data.update({
                "kills": self.kills,
                "deaths": self.deaths,
                "ping": self.ping,
                "dash_cooldown": max(0, self.dash_cooldown_end - time.time())
            })
        
        return data
    
    def __repr__(self):
        return f"Player(id={self.player_id}, name='{self.username}', pos=({self.x:.1f}, {self.y:.1f}))"