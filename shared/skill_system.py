"""
Skill System - Base Classes
Defines the complete skill system architecture with all skill types.
"""

import time
import math
from typing import Optional, Tuple, List, Dict
from enum import Enum, auto


class SkillCategory(Enum):
    """Skill categories/types."""
    SKILLSHOT = auto()      # Linear projectile aimed with mouse
    AOE = auto()            # Area of effect at cursor position
    RANGEBASED = auto()     # Area around player
    HOMING = auto()         # Tracks target automatically
    CHANNELING = auto()     # Continuous effect while held
    DEFENSIVE = auto()      # Shields/damage reduction
    PASSIVE = auto()        # Always active
    CROWD_CONTROL = auto()  # CC effects (can be combined with others)


class CrowdControlType(Enum):
    """Types of crowd control effects."""
    STUN = auto()       # Cannot move or act
    SLOW = auto()       # Reduced movement speed
    ROOT = auto()       # Cannot move but can act
    SILENCE = auto()    # Cannot use skills
    KNOCKBACK = auto()  # Pushed away
    PULL = auto()       # Pulled toward


class SkillState(Enum):
    """Skill activation states."""
    READY = auto()
    COOLDOWN = auto()
    CHANNELING = auto()
    ACTIVE = auto()


class Skill:
    """
    Base skill class - all skills inherit from this.
    
    Attributes:
        skill_id: Unique identifier
        name: Skill name
        category: Type of skill
        damage: Base damage dealt
        mana_cost: Mana required to use
        cooldown: Cooldown time in seconds
        cast_range: Maximum range for targeting
        description: Skill description
    """
    
    def __init__(
        self,
        skill_id: str,
        name: str,
        category: SkillCategory,
        damage: float = 0,
        mana_cost: float = 0,
        cooldown: float = 5.0,
        cast_range: float = 500,
        description: str = ""
    ):
        self.skill_id = skill_id
        self.name = name
        self.category = category
        self.damage = damage
        self.mana_cost = mana_cost
        self.cooldown = cooldown
        self.cast_range = cast_range
        self.description = description
        
        # Runtime state
        self.state = SkillState.READY
        self.cooldown_end_time = 0
        self.last_cast_time = 0
        self.channel_start_time = 0
        
        # CC properties (optional)
        self.cc_type: Optional[CrowdControlType] = None
        self.cc_duration: float = 0
    
    def can_cast(self, current_mana: float) -> Tuple[bool, str]:
        """
        Check if skill can be cast.
        Returns (can_cast, reason_if_not)
        """
        if self.state == SkillState.COOLDOWN:
            remaining = self.get_cooldown_remaining()
            return False, f"On cooldown ({remaining:.1f}s)"
        
        if current_mana < self.mana_cost:
            return False, f"Not enough mana ({self.mana_cost} required)"
        
        return True, ""
    
    def start_cooldown(self):
        """Start the cooldown timer."""
        self.state = SkillState.COOLDOWN
        self.cooldown_end_time = time.time() + self.cooldown
        self.last_cast_time = time.time()
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time."""
        if self.state != SkillState.COOLDOWN:
            return 0
        
        remaining = self.cooldown_end_time - time.time()
        if remaining <= 0:
            self.state = SkillState.READY
            return 0
        
        return remaining
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """
        Cast the skill (override in subclasses).
        
        Args:
            caster_pos: (x, y) position of caster
            target_pos: (x, y) target position (mouse cursor)
            **kwargs: Additional parameters
        
        Returns:
            Skill effect data (varies by skill type)
        """
        raise NotImplementedError("Subclasses must implement cast()")
    
    def update(self, delta_time: float, caster, **kwargs):
        """Update skill state (for channeling, passive, etc.)"""
        pass
    
    def to_dict(self) -> dict:
        """Serialize skill data for networking."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category.name,
            "damage": self.damage,
            "mana_cost": self.mana_cost,
            "cooldown": self.cooldown,
            "cooldown_remaining": self.get_cooldown_remaining(),
            "state": self.state.name,
            "cast_range": self.cast_range
        }


class SkillshotSkill(Skill):
    """
    Skillshot - Linear projectile aimed with mouse cursor.
    
    Example: Fireball that travels in a straight line
    """
    
    def __init__(self, skill_id: str, name: str, damage: float, speed: float = 600,
                 mana_cost: float = 20, cooldown: float = 3.0, max_range: float = 800,
                 projectile_width: float = 20, piercing: bool = False):
        super().__init__(skill_id, name, SkillCategory.SKILLSHOT, damage, mana_cost,
                        cooldown, max_range, "Linear projectile skill")
        
        self.speed = speed  # Projectile speed
        self.max_range = max_range
        self.projectile_width = projectile_width
        self.piercing = piercing  # Can hit multiple targets
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Cast skillshot projectile."""
        # Calculate direction vector
        dx = target_pos[0] - caster_pos[0]
        dy = target_pos[1] - caster_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            dx, dy = 1, 0
        else:
            dx /= distance
            dy /= distance
        
        self.start_cooldown()
        
        return {
            "type": "skillshot",
            "start_x": caster_pos[0],
            "start_y": caster_pos[1],
            "direction_x": dx,
            "direction_y": dy,
            "speed": self.speed,
            "damage": self.damage,
            "max_range": self.max_range,
            "width": self.projectile_width,
            "piercing": self.piercing,
            "skill_id": self.skill_id
        }


class AOESkill(Skill):
    """
    AOE (Area of Effect) - Damage/effect in circular area at cursor position.
    
    Example: Meteor strike at target location
    """
    
    def __init__(self, skill_id: str, name: str, damage: float, radius: float = 150,
                 mana_cost: float = 30, cooldown: float = 8.0, cast_range: float = 600,
                 delay: float = 0.5):
        super().__init__(skill_id, name, SkillCategory.AOE, damage, mana_cost,
                        cooldown, cast_range, "Area of effect skill")
        
        self.radius = radius
        self.delay = delay  # Time before damage applies
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Cast AOE at target position."""
        # Check if target is in range
        dx = target_pos[0] - caster_pos[0]
        dy = target_pos[1] - caster_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > self.cast_range:
            # Clamp to max range
            ratio = self.cast_range / distance
            target_pos = (
                caster_pos[0] + dx * ratio,
                caster_pos[1] + dy * ratio
            )
        
        self.start_cooldown()
        
        return {
            "type": "aoe",
            "center_x": target_pos[0],
            "center_y": target_pos[1],
            "radius": self.radius,
            "damage": self.damage,
            "delay": self.delay,
            "activation_time": time.time() + self.delay,
            "skill_id": self.skill_id
        }


class RangeBasedSkill(Skill):
    """
    Range-Based - Effect around the player (circular area).
    
    Example: Nova that damages all enemies around player
    """
    
    def __init__(self, skill_id: str, name: str, damage: float, radius: float = 200,
                 mana_cost: float = 25, cooldown: float = 6.0):
        super().__init__(skill_id, name, SkillCategory.RANGEBASED, damage, mana_cost,
                        cooldown, radius, "Area around player")
        
        self.radius = radius
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Cast effect around player."""
        self.start_cooldown()
        
        return {
            "type": "rangebased",
            "center_x": caster_pos[0],
            "center_y": caster_pos[1],
            "radius": self.radius,
            "damage": self.damage,
            "skill_id": self.skill_id
        }


class HomingSkill(Skill):
    """
    Homing - Projectile that automatically tracks nearest target.
    
    Example: Magic missile that follows enemies
    """
    
    def __init__(self, skill_id: str, name: str, damage: float, speed: float = 300,
                 mana_cost: float = 15, cooldown: float = 4.0, turn_rate: float = 180,
                 max_lifetime: float = 5.0):
        super().__init__(skill_id, name, SkillCategory.HOMING, damage, mana_cost,
                        cooldown, 1000, "Auto-tracking projectile")
        
        self.speed = speed
        self.turn_rate = turn_rate  # Degrees per second
        self.max_lifetime = max_lifetime
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Launch homing projectile."""
        # Initial direction toward cursor
        dx = target_pos[0] - caster_pos[0]
        dy = target_pos[1] - caster_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            dx, dy = 1, 0
        else:
            dx /= distance
            dy /= distance
        
        self.start_cooldown()
        
        return {
            "type": "homing",
            "start_x": caster_pos[0],
            "start_y": caster_pos[1],
            "direction_x": dx,
            "direction_y": dy,
            "speed": self.speed,
            "damage": self.damage,
            "turn_rate": self.turn_rate,
            "max_lifetime": self.max_lifetime,
            "spawn_time": time.time(),
            "skill_id": self.skill_id
        }


class ChannelingSkill(Skill):
    """
    Channeling - Continuous effect while button held (drains mana over time).
    
    Example: Laser beam that deals continuous damage
    """
    
    def __init__(self, skill_id: str, name: str, damage_per_second: float,
                 mana_per_second: float = 20, cooldown: float = 2.0,
                 max_range: float = 400, beam_width: float = 30):
        super().__init__(skill_id, name, SkillCategory.CHANNELING, damage_per_second,
                        0, cooldown, max_range, "Hold to channel")
        
        self.damage_per_second = damage_per_second
        self.mana_per_second = mana_per_second
        self.beam_width = beam_width
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Start channeling."""
        self.state = SkillState.CHANNELING
        self.channel_start_time = time.time()
        
        # Calculate direction
        dx = target_pos[0] - caster_pos[0]
        dy = target_pos[1] - caster_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            dx, dy = 1, 0
        else:
            dx /= distance
            dy /= distance
        
        return {
            "type": "channeling",
            "start_x": caster_pos[0],
            "start_y": caster_pos[1],
            "direction_x": dx,
            "direction_y": dy,
            "damage_per_second": self.damage_per_second,
            "max_range": self.cast_range,
            "width": self.beam_width,
            "skill_id": self.skill_id,
            "active": True
        }
    
    def update_channel(self, delta_time: float, caster, target_pos: Tuple[float, float]):
        """Update channeling effect (called every frame while active)."""
        if self.state != SkillState.CHANNELING:
            return None
        
        # Calculate mana cost this frame
        mana_cost_this_frame = self.mana_per_second * delta_time
        
        # Check if player has enough mana
        if caster.mana < mana_cost_this_frame:
            return self.stop_channel()
        
        # Consume mana
        caster.mana -= mana_cost_this_frame
        
        # Update direction to follow cursor
        dx = target_pos[0] - caster.x
        dy = target_pos[1] - caster.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx /= distance
            dy /= distance
        
        return {
            "type": "channeling",
            "start_x": caster.x,
            "start_y": caster.y,
            "direction_x": dx,
            "direction_y": dy,
            "damage_per_second": self.damage_per_second,
            "max_range": self.cast_range,
            "width": self.beam_width,
            "skill_id": self.skill_id,
            "active": True
        }
    
    def stop_channel(self):
        """Stop channeling."""
        self.start_cooldown()
        return {
            "type": "channeling",
            "skill_id": self.skill_id,
            "active": False
        }


class DefensiveSkill(Skill):
    """
    Defensive - Shield/damage reduction for duration or number of hits.
    
    Example: Shield that absorbs next 3 hits or lasts 5 seconds
    """
    
    def __init__(self, skill_id: str, name: str, shield_amount: float = 50,
                 duration: float = 3.0, max_hits: int = 0, mana_cost: float = 30,
                 cooldown: float = 15.0):
        super().__init__(skill_id, name, SkillCategory.DEFENSIVE, 0, mana_cost,
                        cooldown, 0, "Defensive shield")
        
        self.shield_amount = shield_amount  # Damage absorbed
        self.duration = duration
        self.max_hits = max_hits  # 0 = unlimited hits, just duration
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Activate shield."""
        self.start_cooldown()
        
        return {
            "type": "defensive",
            "shield_amount": self.shield_amount,
            "duration": self.duration,
            "max_hits": self.max_hits,
            "activation_time": time.time(),
            "hits_remaining": self.max_hits,
            "skill_id": self.skill_id
        }


class PassiveSkill(Skill):
    """
    Passive - Always active, provides permanent bonus.
    
    Example: +20% movement speed, +10% damage
    """
    
    def __init__(self, skill_id: str, name: str, stat_bonuses: Dict[str, float]):
        super().__init__(skill_id, name, SkillCategory.PASSIVE, 0, 0, 0, 0,
                        "Passive bonus")
        
        # stat_bonuses example: {"speed": 1.2, "damage": 1.1, "health_regen": 5}
        self.stat_bonuses = stat_bonuses
        self.state = SkillState.ACTIVE  # Always active
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Passives don't need to be cast."""
        return {
            "type": "passive",
            "stat_bonuses": self.stat_bonuses,
            "skill_id": self.skill_id
        }
    
    def apply_bonuses(self, base_stats: Dict[str, float]) -> Dict[str, float]:
        """Apply passive bonuses to base stats."""
        modified_stats = base_stats.copy()
        
        for stat, bonus in self.stat_bonuses.items():
            if stat in modified_stats:
                if stat.endswith("_multiplier"):
                    # Multiplicative bonus
                    modified_stats[stat] *= bonus
                else:
                    # Additive bonus
                    modified_stats[stat] += bonus
        
        return modified_stats


class CrowdControlSkill(Skill):
    """
    Crowd Control - Stun, slow, silence, etc.
    Can be standalone or added to other skills.
    
    Example: Freeze that stuns target for 2 seconds
    """
    
    def __init__(self, skill_id: str, name: str, cc_type: CrowdControlType,
                 duration: float = 2.0, intensity: float = 1.0, radius: float = 100,
                 mana_cost: float = 40, cooldown: float = 12.0):
        super().__init__(skill_id, name, SkillCategory.CROWD_CONTROL, 0, mana_cost,
                        cooldown, radius, f"Apply {cc_type.name}")
        
        self.cc_type = cc_type
        self.cc_duration = duration
        self.intensity = intensity  # For slows: 0.5 = 50% slow
        self.radius = radius
    
    def cast(self, caster_pos: Tuple[float, float], target_pos: Tuple[float, float], **kwargs):
        """Apply crowd control effect."""
        self.start_cooldown()
        
        return {
            "type": "crowd_control",
            "cc_type": self.cc_type.name,
            "center_x": target_pos[0],
            "center_y": target_pos[1],
            "radius": self.radius,
            "duration": self.cc_duration,
            "intensity": self.intensity,
            "skill_id": self.skill_id
        }