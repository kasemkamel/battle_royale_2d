"""
Skill Database
Central storage for all available skills in the game.
Loads on server startup and provides skill definitions.
"""

from shared.skill_system import (
    SkillshotSkill, AOESkill, RangeBasedSkill, HomingSkill,
    ChannelingSkill, DefensiveSkill, PassiveSkill, CrowdControlSkill,
    CrowdControlType
)
from typing import Dict, List, Optional


class SkillDatabase:
    """
    Central repository for all game skills.
    Skills are defined here and loaded on server startup.
    """
    
    def __init__(self):
        self.skills: Dict[str, any] = {}  # skill_id -> Skill instance
        self._initialize_skills()
    
    def _initialize_skills(self):
        """Initialize all available skills."""
        print("[SkillDB] Initializing skill database...")
        
        # ==================== SKILLSHOT SKILLS ====================
        
        self.skills["fireball"] = SkillshotSkill(
            skill_id="fireball",
            name="Fireball",
            damage=35,
            speed=600,
            mana_cost=20,
            cooldown=3.0,
            max_range=800,
            projectile_width=20,
            piercing=False
        )
        
        self.skills["ice_arrow"] = SkillshotSkill(
            skill_id="ice_arrow",
            name="Ice Arrow",
            damage=25,
            speed=700,
            mana_cost=25,
            cooldown=5.0,
            max_range=900,
            projectile_width=15,
            piercing=False
        )
        # Add slow effect
        self.skills["ice_arrow"].cc_type = CrowdControlType.SLOW
        self.skills["ice_arrow"].cc_duration = 2.5
        
        self.skills["lightning_bolt"] = SkillshotSkill(
            skill_id="lightning_bolt",
            name="Lightning Bolt",
            damage=50,
            speed=1200,
            mana_cost=35,
            cooldown=8.0,
            max_range=1000,
            projectile_width=15,
            piercing=True  # Pierces through enemies
        )
        
        # ==================== AOE SKILLS ====================
        
        self.skills["meteor"] = AOESkill(
            skill_id="meteor",
            name="Meteor Strike",
            damage=60,
            radius=150,
            mana_cost=40,
            cooldown=10.0,
            cast_range=600,
            delay=0.8
        )
        
        self.skills["poison_cloud"] = AOESkill(
            skill_id="poison_cloud",
            name="Poison Cloud",
            damage=15,  # Lower damage but DoT effect
            radius=200,
            mana_cost=30,
            cooldown=12.0,
            cast_range=500,
            delay=0.3
        )
        
        self.skills["earthquake"] = AOESkill(
            skill_id="earthquake",
            name="Earthquake",
            damage=45,
            radius=250,
            mana_cost=50,
            cooldown=15.0,
            cast_range=400,
            delay=1.0
        )
        # Add stun effect
        self.skills["earthquake"].cc_type = CrowdControlType.STUN
        self.skills["earthquake"].cc_duration = 1.5
        
        # ==================== RANGE-BASED SKILLS ====================
        
        self.skills["frost_nova"] = RangeBasedSkill(
            skill_id="frost_nova",
            name="Frost Nova",
            damage=25,
            radius=200,
            mana_cost=30,
            cooldown=8.0
        )
        self.skills["frost_nova"].cc_type = CrowdControlType.SLOW
        self.skills["frost_nova"].cc_duration = 2.0
        
        self.skills["shockwave"] = RangeBasedSkill(
            skill_id="shockwave",
            name="Shockwave",
            damage=40,
            radius=180,
            mana_cost=35,
            cooldown=10.0
        )
        self.skills["shockwave"].cc_type = CrowdControlType.KNOCKBACK
        
        # ==================== HOMING SKILLS ====================
        
        self.skills["magic_missile"] = HomingSkill(
            skill_id="magic_missile",
            name="Magic Missile",
            damage=20,
            speed=300,
            mana_cost=15,
            cooldown=4.0,
            turn_rate=180,
            max_lifetime=5.0
        )
        
        self.skills["seeking_orb"] = HomingSkill(
            skill_id="seeking_orb",
            name="Seeking Orb",
            damage=30,
            speed=250,
            mana_cost=25,
            cooldown=6.0,
            turn_rate=120,
            max_lifetime=6.0
        )
        
        # ==================== CHANNELING SKILLS ====================
        
        self.skills["laser_beam"] = ChannelingSkill(
            skill_id="laser_beam",
            name="Laser Beam",
            damage_per_second=40,
            mana_per_second=25,
            cooldown=3.0,
            max_range=400,
            beam_width=20
        )
        
        self.skills["flame_thrower"] = ChannelingSkill(
            skill_id="flame_thrower",
            name="Flame Thrower",
            damage_per_second=35,
            mana_per_second=20,
            cooldown=4.0,
            max_range=300,
            beam_width=40
        )
        
        # ==================== DEFENSIVE SKILLS ====================
        
        self.skills["shield"] = DefensiveSkill(
            skill_id="shield",
            name="Protective Shield",
            shield_amount=75,
            duration=5.0,
            max_hits=3,
            mana_cost=35,
            cooldown=20.0
        )
        
        self.skills["barrier"] = DefensiveSkill(
            skill_id="barrier",
            name="Energy Barrier",
            shield_amount=50,
            duration=3.0,
            max_hits=0,  # Duration-based only
            mana_cost=25,
            cooldown=15.0
        )
        
        self.skills["iron_skin"] = DefensiveSkill(
            skill_id="iron_skin",
            name="Iron Skin",
            shield_amount=100,
            duration=4.0,
            max_hits=5,
            mana_cost=40,
            cooldown=25.0
        )
        
        # ==================== PASSIVE SKILLS ====================
        
        self.skills["swift_footed"] = PassiveSkill(
            skill_id="swift_footed",
            name="Swift Footed",
            stat_bonuses={
                "speed_multiplier": 1.15,  # +15% speed
                "mana_regen": 2
            }
        )
        
        self.skills["tough_skin"] = PassiveSkill(
            skill_id="tough_skin",
            name="Tough Skin",
            stat_bonuses={
                "max_health": 20,  # +20 max health
                "health_regen": 1
            }
        )
        
        self.skills["arcane_mind"] = PassiveSkill(
            skill_id="arcane_mind",
            name="Arcane Mind",
            stat_bonuses={
                "max_mana": 20,  # +20 max mana
                "mana_regen": 3
            }
        )
        
        # ==================== CROWD CONTROL SKILLS ====================
        
        self.skills["ice_prison"] = CrowdControlSkill(
            skill_id="ice_prison",
            name="Ice Prison",
            cc_type=CrowdControlType.STUN,
            duration=2.5,
            radius=120,
            mana_cost=50,
            cooldown=15.0
        )
        
        self.skills["entangle"] = CrowdControlSkill(
            skill_id="entangle",
            name="Entangle",
            cc_type=CrowdControlType.ROOT,
            duration=3.0,
            radius=100,
            mana_cost=40,
            cooldown=12.0
        )
        
        self.skills["silence"] = CrowdControlSkill(
            skill_id="silence",
            name="Silence",
            cc_type=CrowdControlType.SILENCE,
            duration=3.5,
            radius=150,
            mana_cost=45,
            cooldown=18.0
        )
        
        print(f"[SkillDB] Loaded {len(self.skills)} skills")
    
    def get_skill(self, skill_id: str) -> Optional[any]:
        """Get a skill by ID."""
        return self.skills.get(skill_id)
    
    def get_all_skills(self) -> List[dict]:
        """Get all skills as serializable dictionaries."""
        return [
            {
                **skill.to_dict(),
                "description": skill.description
            }
            for skill in self.skills.values()
        ]
    
    def get_skills_by_category(self, category: str) -> List[dict]:
        """Get all skills of a specific category."""
        return [
            {
                **skill.to_dict(),
                "description": skill.description
            }
            for skill in self.skills.values()
            if skill.category.name == category
        ]
    
    def create_skill_instance(self, skill_id: str) -> Optional[any]:
        """
        Create a fresh instance of a skill.
        Important: Each player needs their own skill instances for cooldowns.
        """
        base_skill = self.skills.get(skill_id)
        if not base_skill:
            return None
        
        # Import the skill class type
        skill_class = type(base_skill)
        
        # Create new instance with same parameters
        # This is a simplified approach - in production, you'd store skill configs
        # and instantiate from config data
        
        # For now, we'll just return a reference (in production, deep copy or recreate)
        return base_skill
    
    def validate_skill_loadout(self, skill_ids: List[str]) -> tuple:
        """
        Validate a player's skill loadout.
        Returns (is_valid, error_message)
        """
        if len(skill_ids) > 4:
            return False, "Maximum 4 skills allowed"
        
        # Check for duplicates
        if len(skill_ids) != len(set(skill_ids)):
            return False, "Duplicate skills not allowed"
        
        # Check if all skills exist
        for skill_id in skill_ids:
            if skill_id not in self.skills:
                return False, f"Unknown skill: {skill_id}"
        
        return True, ""


# Global skill database instance
_skill_db = None

def get_skill_database() -> SkillDatabase:
    """Get or create the global skill database."""
    global _skill_db
    if _skill_db is None:
        _skill_db = SkillDatabase()
    return _skill_db