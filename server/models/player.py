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
    PLAYER_SPRINT_MULTIPLIER, PLAYER_SPRINT_MANA_COST,
    PLAYER_DASH_SPEED, PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN, PLAYER_DASH_MANA_COST
)


class Player:
    """Server-side player instance."""
    
    def __init__(self, player_id: int, user_id: int, username: str):
        # Identity
        self.player_id = player_id
        self.user_id = user_id
        self.username = username

        self.level = 0
        self.max_level = 10
        self.experience = 0
        self.experience_to_next_level = 100

        # State
        self.state = PlayerState.CONNECTED
        self.character_class = CharacterClass.WARRIOR
        
        # Position and movement
        self.x = 0.0
        self.y = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.rotation = 0.0
        
        # Movement modifiers
        self.is_sprinting = False
        self.is_dashing = False
        self.dash_direction_x = 0.0
        self.dash_direction_y = 0.0
        self.dash_end_time = 0.0
        self.dash_cooldown_end = 0.0
        
        # Combat - BASE VALUES (before passive bonuses)
        self.base_max_health = PLAYER_MAX_HEALTH
        self.base_max_mana = PLAYER_MAX_MANA
        self.base_speed = PLAYER_SPEED
        self.base_mana_regen = PLAYER_MANA_REGEN
        
        # Combat - CURRENT VALUES (after passive bonuses)
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
        self.active_effects = []
        self.skill_cooldowns = [0.0, 0.0, 0.0, 0.0]
        
        # Channeling state
        self.is_channeling = False
        self.channeling_skill_index = None
        self.channeling_skill = None
        self.channel_target_x = 0
        self.channel_target_y = 0
        
        # Passive bonuses (applied from passive skills)
        self.passive_bonuses_applied = False
        self.passive_speed_multiplier = 1.0
        self.passive_mana_regen = 0.0
        self.passive_health_regen = 0.0
        self.passive_damage_multiplier = 1.0
        
        # Defense
        self.defense = 0.0
        self.defense_max_hits = 0
        self.defense_end_time = 0.0
        
        self.is_invisible = False
        self.invisibility_end_time = 0.0

        # Continuous damage
        self.continuous_damage = 0.0
        self.continuous_damage_end_time = 0.0
        self.continuous_attacker_id = None
        
        # Crowd Control
        self.is_stunned = False
        self.stun_end_time = 0
        self.movement_speed_multiplier = 1.0
        
        # Input
        self.input_x = 0.0
        self.input_y = 0.0
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.actions = {}
        
        # Network
        self.last_update = time.time()
        self.ping = 0
        
        # Ready state (for lobby)
        self.ready = False

        self.add_experience(100)
    
    def apply_passive_bonuses(self):
        """
        Apply stat bonuses from all equipped passive skills.
        
        This function should be called ONCE after skills are loaded (before match starts).
        It scans all equipped skills, finds passives, and applies their bonuses to the player.
        
        Bonuses handled:
        - speed_multiplier: Multiplicative speed bonus (e.g., 1.15 = +15% speed)
        - max_health_multiplier: Multiplicative max health bonus (e.g., 1.2 = +20% max HP)
        - max_mana: Additive max mana bonus (e.g., 20 = +20 max mana)
        - health: Immediate health bonus (e.g., 20 = +20 HP now)
        - mana_regen: Additive mana regen per second (e.g., 3 = +3 mana/s)
        - health_regen: Additive health regen per second (e.g., 1 = +1 HP/s)
        - damage_multiplier: Multiplicative damage bonus (e.g., 1.1 = +10% damage)
        
        Returns:
            bool: True if bonuses were applied, False if already applied
        """
        # Prevent double application
        if self.passive_bonuses_applied:
            print(f"[Player] {self.username} passive bonuses already applied, skipping")
            return False
        
        from shared.skill_system import SkillCategory
        
        # Count passive skills for logging
        passive_count = sum(1 for skill in self.skills if skill.category == SkillCategory.PASSIVE)
        
        if passive_count == 0:
            print(f"[Player] {self.username} has no passive skills, skipping bonuses")
            self.passive_bonuses_applied = True
            return True
        
        print(f"[Player] {self.username} applying {passive_count} passive skill bonuses...")
        
        # Initialize bonus accumulators
        # Multiplicative bonuses start at 1.0 (100%)
        speed_multiplier = 1.0
        max_health_multiplier = 1.0
        damage_multiplier = 1.0
        
        # Additive bonuses start at 0
        max_mana_bonus = 0
        health_bonus = 0
        mana_regen_bonus = 0
        health_regen_bonus = 0
        
        # Scan all equipped skills for passive bonuses
        for skill in self.skills:
            if skill.category != SkillCategory.PASSIVE:
                continue
            
            print(f"  - Processing passive: {skill.name}")
            
            # Get stat bonuses from this passive skill
            bonuses = skill.stat_bonuses
            
            # Accumulate multiplicative bonuses (multiply together)
            # Example: Two +15% speed passives → 1.15 × 1.15 = 1.3225 (32.25% total)
            if "speed_multiplier" in bonuses:
                speed_multiplier *= bonuses["speed_multiplier"]
                print(f"    • Speed: ×{bonuses['speed_multiplier']:.2f}")
            
            if "max_health_multiplier" in bonuses:
                max_health_multiplier *= bonuses["max_health_multiplier"]
                print(f"    • Max Health: ×{bonuses['max_health_multiplier']:.2f}")
            
            if "damage_multiplier" in bonuses:
                damage_multiplier *= bonuses["damage_multiplier"]
                print(f"    • Damage: ×{bonuses['damage_multiplier']:.2f}")
            
            # Accumulate additive bonuses (add together)
            # Example: Two +20 mana passives → 20 + 20 = 40 total
            if "max_mana" in bonuses:
                max_mana_bonus += bonuses["max_mana"]
                print(f"    • Max Mana: +{bonuses['max_mana']}")
            
            if "health" in bonuses:
                health_bonus += bonuses["health"]
                print(f"    • Immediate Health: +{bonuses['health']}")
            
            if "mana_regen" in bonuses:
                mana_regen_bonus += bonuses["mana_regen"]
                print(f"    • Mana Regen: +{bonuses['mana_regen']}/s")
            
            if "health_regen" in bonuses:
                health_regen_bonus += bonuses["health_regen"]
                print(f"    • Health Regen: +{bonuses['health_regen']}/s")
        
        # ===== APPLY BONUSES TO PLAYER STATS =====
        
        # Store old values for logging
        old_max_health = self.max_health
        old_max_mana = self.max_mana
        
        # Apply max health multiplier
        self.max_health = int(self.base_max_health * max_health_multiplier)
        
        # Apply max mana bonus (additive)
        self.max_mana = int(self.base_max_mana + max_mana_bonus)
        
        # ===== HANDLE CURRENT HEALTH/MANA =====
        # Important: Don't punish players for equipping passives mid-game
        
        # Calculate health percentage before bonus
        health_percentage = self.health / old_max_health if old_max_health > 0 else 1.0
        
        # If player was at full health, keep them at full health
        if health_percentage >= 0.99:  # Allow for rounding errors
            self.health = self.max_health
        else:
            # Scale current health proportionally to new max
            # Example: Had 50/100 HP, max becomes 120 → now 60/120 HP (same 50%)
            self.health = int(self.health * (self.max_health / old_max_health))
        
        # Apply immediate health bonus (from "health" stat)
        if health_bonus > 0:
            self.health = min(self.max_health, self.health + health_bonus)
        
        # Ensure health doesn't exceed new maximum
        self.health = min(self.max_health, self.health)
        
        # Same logic for mana
        mana_percentage = self.mana / old_max_mana if old_max_mana > 0 else 1.0
        
        if mana_percentage >= 0.99:
            self.mana = self.max_mana
        else:
            self.mana = self.mana * (self.max_mana / old_max_mana)
        
        # Ensure mana doesn't exceed new maximum
        self.mana = min(self.max_mana, self.mana)
        
        # ===== STORE PASSIVE MODIFIERS =====
        # These are used in update() for ongoing effects
        
        self.passive_speed_multiplier = speed_multiplier
        self.passive_mana_regen = mana_regen_bonus
        self.passive_health_regen = health_regen_bonus
        self.passive_damage_multiplier = damage_multiplier
        
        # Mark as applied to prevent double-application
        self.passive_bonuses_applied = True
        
        # ===== LOG FINAL RESULTS =====
        print(f"[Player] {self.username} passive bonuses applied successfully:")
        print(f"  • Max Health: {old_max_health} → {self.max_health} ({self.max_health - old_max_health:+d})")
        print(f"  • Max Mana: {old_max_mana} → {self.max_mana} ({self.max_mana - old_max_mana:+d})")
        print(f"  • Current Health: {int(self.health)}/{self.max_health}")
        print(f"  • Current Mana: {int(self.mana)}/{self.max_mana}")
        print(f"  • Speed Multiplier: ×{speed_multiplier:.2f}")
        print(f"  • Damage Multiplier: ×{damage_multiplier:.2f}")
        print(f"  • Mana Regen: {PLAYER_MANA_REGEN + mana_regen_bonus:.1f}/s")
        print(f"  • Health Regen: {health_regen_bonus:.1f}/s")
        
        return True
    
    def get_effective_speed(self) -> float:
        """
        Calculate player's effective speed including all modifiers.
        
        Returns:
            float: Effective speed in pixels per second
        """
        speed = self.base_speed
        
        # Apply passive speed bonus
        speed *= self.passive_speed_multiplier
        
        # Apply temporary speed modifiers (slows, buffs)
        speed *= self.movement_speed_multiplier
        
        # Apply sprint multiplier
        if self.is_sprinting:
            speed *= PLAYER_SPRINT_MULTIPLIER
        
        return speed
    
    def get_skill_damage(self, base_damage: float) -> float:
        """
        Calculate effective skill damage with passive multipliers.
        
        Args:
            base_damage: Base damage of the skill
            
        Returns:
            float: Effective damage after multipliers
        """
        damage = base_damage
        
        # Apply passive damage bonus
        damage *= self.passive_damage_multiplier
        
        return damage
    
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
                self.vel_x = self.dash_direction_x * PLAYER_DASH_SPEED
                self.vel_y = self.dash_direction_y * PLAYER_DASH_SPEED
                self.x += self.vel_x * delta_time
                self.y += self.vel_y * delta_time
                return

        # Check stun
        if self.is_stunned:
            if time.time() >= self.stun_end_time:
                self.is_stunned = False
            else:
                self.vel_x = 0
                self.vel_y = 0
                return
        
        # Update defense
        if self.defense > 0:
            if time.time() >= self.defense_end_time:
                self.defense = 0
                self.defense_max_hits = 0
        
        if self.is_invisible:
            if time.time() >= self.invisibility_end_time:
                self.is_invisible = False

        # Update continuous damage
        if self.continuous_damage > 0:
            if time.time() >= self.continuous_damage_end_time:
                self.continuous_damage = 0
                self.continuous_damage_end_time = 0
                self.continuous_attacker_id = None
            else:
                damage = self.continuous_damage * delta_time
                self.take_damage(damage, self.continuous_attacker_id)
        
        # Update channeling skills
        if self.is_channeling and self.channeling_skill:
            channel_data = self.channeling_skill.update_channel(
                delta_time, 
                self, 
                (self.channel_target_x, self.channel_target_y)
            )
            
            if channel_data and not channel_data.get("active", True):
                # Channeling stopped
                self.is_channeling = False
                self.channeling_skill_index = None
                self.channeling_skill = None
        
        # Update skill cooldowns for network sync
        for i, skill in enumerate(self.skills):
            if i < 4:
                self.skill_cooldowns[i] = skill.get_cooldown_remaining()
        

        
        # Calculate speed with ALL modifiers (base, passive, sprint, slow)
        base_speed = self.get_effective_speed()
        
        # Sprint mana consumption
        if self.is_sprinting:
            mana_cost = PLAYER_SPRINT_MANA_COST * delta_time
            if self.mana >= mana_cost:
                self.mana -= mana_cost
            else:
                self.is_sprinting = False
        
        # Update velocity based on input
        self.vel_x = self.input_x * base_speed
        self.vel_y = self.input_y * base_speed
        
        # Update position
        self.x += self.vel_x * delta_time
        self.y += self.vel_y * delta_time
        
        # Regenerate mana (with passive bonus)
        if self.mana < self.max_mana:
            mana_regen = self.base_mana_regen + self.passive_mana_regen
            self.mana = min(self.max_mana, self.mana + mana_regen * delta_time)
        
        # Regenerate health (from passives only)
        if self.passive_health_regen > 0 and self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.passive_health_regen * delta_time)
        
        # Update timestamp
        self.last_update = time.time()
    
    def _update_rotation(self):
        """Update player rotation to face mouse cursor."""
        dx = self.mouse_x - self.x
        dy = self.mouse_y - self.y
        
        if dx != 0 or dy != 0:
            self.rotation = math.atan2(dy, dx)

    def continuous_damage_tick(self, damage: float, duration: float, attacker_id: int = None):
        """Start a continuous damage effect (e.g., DOT)."""
        if not self.is_alive:
            return False
        self.continuous_damage = damage
        self.continuous_damage_end_time = time.time() + duration
        self.continuous_attacker_id = attacker_id

    def take_damage(self, damage: float, attacker_id: int = None):
        """Apply damage to player."""
        if not self.is_alive:
            return False

        # Apply defense reduction
        if self.defense_max_hits > 0 and self.defense > 0:
            self.defense_max_hits -= 1
            if self.defense_max_hits == 0:
                self.defense = 0.0  # Defense breaks
            reduced_damage = damage - self.defense
        elif self.defense > 0:
            reduced_damage = damage * (100 / (100 + self.defense))
        else:
            reduced_damage = damage
        
        reduced_damage = max(1, int(reduced_damage))
        self.health = max(0, self.health - int(reduced_damage))

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
        if self.mana < PLAYER_DASH_MANA_COST:
            return False
        return True
    
    def start_dash(self):
        """Start dash in direction of mouse cursor."""
        # Check mana
        if self.mana < PLAYER_DASH_MANA_COST:
            return
        print(f"[player] now at ({self.x:.1f}, {self.y:.1f})")
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
        
        # Consume mana
        self.mana -= PLAYER_DASH_MANA_COST
        
        self.is_dashing = True
        self.dash_end_time = time.time() + PLAYER_DASH_DURATION
        self.dash_cooldown_end = time.time() + PLAYER_DASH_COOLDOWN
        
        print(f"[Player] {self.username} dashed (mana: {self.mana:.1f})")

    def can_teleport(self, mana_cost) -> bool:
        """Check if player can teleport."""
        if self.is_stunned:
            return False
        if self.mana < mana_cost:
            return False
        return True

    def teleport(self, distance: float, mana_cost: float = PLAYER_DASH_MANA_COST):
        """Teleport player a certain distance in the direction they are facing."""
        if not self.can_teleport(mana_cost):
            return
        print(f"[player] now at ({self.x:.1f}, {self.y:.1f})")
        # Calculate teleport direction
        dx = math.cos(self.rotation) * distance
        dy = math.sin(self.rotation) * distance

        self.x += dx
        self.y += dy

        # Consume mana
        self.mana -= mana_cost

        print(f"[Player] {self.username} teleported (mana: {self.mana:.1f})")
        print(f"[player] Teleported to ({self.x:.1f}, {self.y:.1f})")
        

    def update(self, delta_time: float):
        """Update player state."""
        # Update dash
        if self.is_dashing:
            if time.time() > self.dash_end_time:
                self.is_dashing = False
                self.dash_direction_x = 0

    def apply_crowd_control(self, cc_type: str, duration: float, intensity: float = 1.0):
        """Apply crowd control effect."""
        if cc_type == "STUN":
            self.is_stunned = True
            self.stun_end_time = time.time() + duration
        elif cc_type == "SLOW":
            self.movement_speed_multiplier = 1.0 - intensity  # intensity = 0.5 means 50% slow
            # TODO: Add timer to remove slow
    
    def apply_defense(self, defense_amount: float, max_hits: int, duration: float):
        """Apply defense buff."""
        self.defense = defense_amount
        self.defense_max_hits = max_hits
        self.defense_end_time = time.time() + duration
    
    def apply_heal(self, heal_amount: float):
        """Apply healing to the player."""
        if not self.is_alive:
            return
        self.health += heal_amount
        if self.health > self.max_health:
            self.health = self.max_health

    def restore_mana(self, amount: float):
        """Restore mana to the player."""
        if not self.is_alive:
            return
        self.mana += amount
        if self.mana > self.max_mana:
            self.mana = self.max_mana

    def apply_invisibility(self, duration: float, speed_bonus: float = 1.0):
        """Apply invisibility to the player."""
        self.is_invisible = True
        self.invisibility_end_time = time.time() + duration
        self.movement_speed_multiplier *= speed_bonus

    def start_channeling(self, skill_index: int, target_x: float, target_y: float):
        """Start channeling a skill."""
        if skill_index >= len(self.skills):
            return False
        
        skill = self.skills[skill_index]
        
        # Check if it's a channeling skill
        from shared.skill_system import SkillCategory
        if skill.category != SkillCategory.CHANNELING:
            return False
        
        # Start channeling
        self.is_channeling = True
        self.channeling_skill_index = skill_index
        self.channeling_skill = skill
        self.channel_target_x = target_x
        self.channel_target_y = target_y
        
        return True
    
    def stop_channeling(self):
        """Stop channeling current skill."""
        if self.is_channeling and self.channeling_skill:
            self.channeling_skill.stop_channel()
        
        self.is_channeling = False
        self.channeling_skill_index = None
        self.channeling_skill = None

    def add_experience(self, amount: int):
        """Add experience points to the player."""
        self.experience += amount
        self.check_for_level_up()

    def check_for_level_up(self):
        """Check and handle level ups."""
        while self.experience >= self.experience_to_next_level and self.level < self.max_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            self.experience_to_next_level = self.calculate_xp_for_next_level()
            self.on_level_up()

    def calculate_xp_for_next_level(self) -> int:
        """Calculate experience required for next level."""
        base = 100
        growth = 1.5
        return int(base * (growth ** (self.level - 1)))

    def on_level_up(self):
        """Handle bonuses on level up."""
        old_max_health = self.base_max_health
        if self.character_class == CharacterClass.WARRIOR:
            charecter_type_health_growth_rate =  20
            self.passive_health_regen += 1.0
            self.passive_damage_multiplier += 0.1

        elif self.character_class == CharacterClass.MAGE:
            charecter_type_health_growth_rate = 15
            self.passive_mana_regen += 0.5
            self.passive_damage_multiplier += 0.15

        elif self.character_class == CharacterClass.ARCHER:
            charecter_type_health_growth_rate = 10
            self.passive_damage_multiplier += 0.2

        elif self.character_class == CharacterClass.ASSASSIN:
            charecter_type_health_growth_rate = 12
            self.passive_speed_multiplier += 0.2
            self.passive_damage_multiplier += 0.4

        self.max_health += charecter_type_health_growth_rate ** (self.level - 1) 
        self.health = self.health / old_max_health * self.max_health
        print(f"[Player] {self.username} leveled up to Level {self.level}!")
        print(f"  • New Max Health: {self.max_health}")
        print(f"  • New Damage Multiplier: {self.passive_damage_multiplier}")
        print(f"  • New Speed Multiplier: {self.passive_speed_multiplier}")
        print(f"  • New Mana Regeneration: {self.passive_mana_regen}")
        print(f"  • New Health Regeneration: {self.passive_health_regen}")

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
            "is_stunned": self.is_stunned,
            "is_invisible": self.is_invisible,
            "skill_cooldowns": [round(cd, 2) for cd in self.skill_cooldowns]
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
    

"""
level 1 needs 100 exp
level 2 needs 150 exp
level 3 needs 225 exp
level 4 needs 337 exp
level 5 needs 506 exp
level 6 needs 759 exp
level 7 needs 1134 exp
level 8 needs 1683 exp
level 9 needs 2513 exp
level 10 is the max level
"""



