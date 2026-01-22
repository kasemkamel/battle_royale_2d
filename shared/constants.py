# shared/constants.py
"""
Shared Constants
Contains all game constants shared between client and server.
This ensures consistency in game mechanics.
"""

# Network Configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555
BUFFER_SIZE = 4096
TICK_RATE = 30  # Server updates per second
NETWORK_UPDATE_RATE = 20  # Client sends input this many times per second

# Game Configuration
GAME_TITLE = "2D Battle Royale"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# World Configuration
WORLD_WIDTH = 3000
WORLD_HEIGHT = 3000
TILE_SIZE = 50

# Player Configuration
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
PLAYER_SPEED = 200  # Pixels per second (base speed)
PLAYER_SPRINT_MULTIPLIER = 1.5  # Sprint is 50% faster
PLAYER_SPRINT_MANA_COST = 5  # Mana per second while sprinting
PLAYER_DASH_SPEED = 800  # Dash speed in pixels/second
PLAYER_DASH_DURATION = 0.2  # Dash lasts 0.2 seconds
PLAYER_DASH_COOLDOWN = 3.0  # Dash cooldown in seconds
PLAYER_DASH_MANA_COST = 15  # Mana cost per dash
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_MANA = 100
PLAYER_MANA_REGEN = 15  # Mana per second
PLAYER_RESPAWN_TIME = 5  # Seconds

# Match Configuration
MIN_PLAYERS = 2  # Minimum players to start a match
MAX_PLAYERS = 50  # Maximum players per match
LOBBY_WAIT_TIME = 10  # Seconds to wait before starting
MATCH_DURATION = 600  # Seconds (10 minutes)

# Zone Configuration (Battle Royale shrinking zone)
ZONE_INITIAL_RADIUS = 1400
ZONE_SHRINK_RATE = 2  # Pixels per second
ZONE_DAMAGE_PER_SECOND = 5

# Skill Configuration
MAX_SKILLS = 4
SKILL_COOLDOWN_DEFAULT = 5.0  # Seconds

# Skill Types Configuration
SKILLSHOT_SPEED = 600  # Projectile speed
SKILLSHOT_MAX_RANGE = 800  # Max distance
AOE_RADIUS_DEFAULT = 150  # Default AOE radius
RANGEBASED_RADIUS = 200  # Radius around player
HOMING_SPEED = 300  # Homing projectile speed
HOMING_TURN_RATE = 180  # Degrees per second
CHANNELING_MANA_COST = 20  # Per second
DEFENSIVE_DURATION = 3.0  # Default shield duration
CROWD_CONTROL_DURATION = 2.0  # Default CC duration

# Colors (RGB)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)

# UI Colors
UI_BG_COLOR = (30, 30, 40)
UI_BUTTON_COLOR = (70, 130, 180)
UI_BUTTON_HOVER = (100, 149, 237)
UI_TEXT_COLOR = (255, 255, 255)
UI_ACCENT_COLOR = (255, 215, 0)