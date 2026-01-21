# shared/enums.py
"""
Shared Enumerations
Defines all enumerated types used across client and server.
"""

from enum import Enum, auto


class PacketType(Enum):
    """Types of network packets exchanged between client and server."""
    
    # Connection
    CONNECT = auto()
    DISCONNECT = auto()
    PING = auto()
    PONG = auto()
    
    # Authentication
    LOGIN_REQUEST = auto()
    LOGIN_RESPONSE = auto()
    REGISTER_REQUEST = auto()
    REGISTER_RESPONSE = auto()
    LOGOUT = auto()
    
    # Lobby
    JOIN_LOBBY = auto()
    LEAVE_LOBBY = auto()
    LOBBY_STATE = auto()
    PLAYER_READY = auto()
    GAME_START = auto()
    
    # Gameplay
    PLAYER_INPUT = auto()
    WORLD_STATE = auto()
    PLAYER_MOVE = auto()
    PLAYER_ATTACK = auto()
    USE_SKILL = auto()
    PLAYER_DAMAGED = auto()
    PLAYER_DIED = auto()
    PLAYER_RESPAWN = auto()
    
    # Skills
    GET_ALL_SKILLS = auto()
    ALL_SKILLS_RESPONSE = auto()
    UPDATE_SKILL_LOADOUT = auto()
    SKILL_LOADOUT_RESPONSE = auto()
    
    # Chat
    CHAT_MESSAGE = auto()
    
    # Match
    MATCH_END = auto()
    MATCH_STATS = auto()


class PlayerState(Enum):
    """Player connection and game states."""
    DISCONNECTED = auto()
    CONNECTED = auto()
    LOBBY = auto()
    IN_GAME = auto()
    SPECTATING = auto()
    DEAD = auto()


class GameState(Enum):
    """Overall game states for client."""
    MENU = auto()
    LOBBY = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class MatchState(Enum):
    """Server-side match states."""
    WAITING = auto()
    STARTING = auto()
    ACTIVE = auto()
    ENDING = auto()
    FINISHED = auto()


class CharacterClass(Enum):
    """Playable character classes."""
    WARRIOR = auto()
    MAGE = auto()
    ARCHER = auto()
    ASSASSIN = auto()


class SkillType(Enum):
    """Types of skills/abilities."""
    ATTACK = auto()
    DEFENSE = auto()
    MOVEMENT = auto()
    UTILITY = auto()


class Direction(Enum):
    """Movement directions."""
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    NONE = auto()