# server/models/projectile.py
"""
Projectile Model
Represents moving projectiles (skillshots, homing missiles, etc.)
"""

import time
import math
from typing import Optional, Tuple


class Projectile:
    """Base projectile that moves through the world."""
    
    def __init__(self, projectile_id: int, skill_id: str, caster_id: int,
                 x: float, y: float, direction_x: float, direction_y: float,
                 speed: float, damage: float, max_range: float, width: float,
                 piercing: bool = False):
        self.projectile_id = projectile_id
        self.skill_id = skill_id
        self.caster_id = caster_id
        
        # Position and movement
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = speed
        
        # Properties
        self.damage = damage
        self.max_range = max_range
        self.width = width
        self.piercing = piercing
        
        # State
        self.is_alive = True
        self.spawn_time = time.time()
        self.hit_players = set()  # Track hits for piercing
    
    def update(self, delta_time: float):
        """Update projectile position."""
        if not self.is_alive:
            return
        
        # Move projectile
        self.x += self.direction_x * self.speed * delta_time
        self.y += self.direction_y * self.speed * delta_time
        
        # Check if exceeded max range
        distance_traveled = math.sqrt(
            (self.x - self.start_x)**2 + (self.y - self.start_y)**2
        )
        
        if distance_traveled >= self.max_range:
            self.is_alive = False
    
    def check_collision(self, player) -> bool:
        """
        Check if projectile hit a player.
        Returns True if hit and should be destroyed.
        """
        if not self.is_alive or not player.is_alive:
            return False
        
        # Don't hit caster
        if player.player_id == self.caster_id:
            return False
        
        # Don't hit same player twice (for piercing)
        if player.player_id in self.hit_players:
            return False
        
        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check collision (projectile width + player radius)
        if distance <= self.width + 20:  # 20 = player radius
            # Apply damage
            player.take_damage(self.damage, self.caster_id)
            self.hit_players.add(player.player_id)
            
            # Destroy projectile if not piercing
            if not self.piercing:
                self.is_alive = False
            
            return True
        
        return False
    
    def to_dict(self) -> dict:
        """Serialize for network transmission."""
        return {
            "projectile_id": self.projectile_id,
            "skill_id": self.skill_id,
            "caster_id": self.caster_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "direction_x": round(self.direction_x, 2),
            "direction_y": round(self.direction_y, 2),
            "width": self.width
        }


class HomingProjectile(Projectile):
    """Projectile that tracks the nearest enemy."""
    
    def __init__(self, projectile_id: int, skill_id: str, caster_id: int,
                 x: float, y: float, direction_x: float, direction_y: float,
                 speed: float, damage: float, turn_rate: float, max_lifetime: float):
        super().__init__(
            projectile_id, skill_id, caster_id, x, y, 
            direction_x, direction_y, speed, damage, 
            max_range=999999,  # No range limit, use lifetime instead
            width=15, piercing=False
        )
        self.turn_rate = turn_rate  # Degrees per second
        self.max_lifetime = max_lifetime
        self.target_id: Optional[int] = None
    
    def update(self, delta_time: float, players: dict):
        """Update with homing behavior."""
        if not self.is_alive:
            return
        
        # Check lifetime
        if time.time() - self.spawn_time >= self.max_lifetime:
            self.is_alive = False
            return
        
        # Find nearest target
        target = self._find_target(players)
        
        if target:
            # Calculate desired direction to target
            dx = target.x - self.x
            dy = target.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                desired_dir_x = dx / distance
                desired_dir_y = dy / distance
                
                # Calculate angle difference
                current_angle = math.atan2(self.direction_y, self.direction_x)
                desired_angle = math.atan2(desired_dir_y, desired_dir_x)
                
                # Turn towards target (limited by turn rate)
                angle_diff = desired_angle - current_angle
                
                # Normalize angle to [-pi, pi]
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                
                # Apply turn rate limit
                max_turn = math.radians(self.turn_rate) * delta_time
                angle_diff = max(-max_turn, min(max_turn, angle_diff))
                
                # Update direction
                new_angle = current_angle + angle_diff
                self.direction_x = math.cos(new_angle)
                self.direction_y = math.sin(new_angle)
        
        # Move projectile
        self.x += self.direction_x * self.speed * delta_time
        self.y += self.direction_y * self.speed * delta_time
    
    def _find_target(self, players: dict):
        """Find nearest valid target."""
        nearest_target = None
        min_distance = float('inf')
        
        for player in players.values():
            if not player.is_alive:
                continue
            if player.player_id == self.caster_id:
                continue
            
            dx = player.x - self.x
            dy = player.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_target = player
        
        return nearest_target