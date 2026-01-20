# client/models/player.py
"""
Player Model (Client)
Client-side representation of a player for rendering and display.
"""

import pygame
from shared.constants import PLAYER_WIDTH, PLAYER_HEIGHT, COLOR_BLUE, COLOR_RED, COLOR_GREEN


class Player:
    """Client-side player model for rendering."""
    
    def __init__(self, player_id: int, username: str, x: float = 0, y: float = 0):
        self.player_id = player_id
        self.username = username
        
        # Position
        self.x = x
        self.y = y
        self.rotation = 0
        
        # Display
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.color = COLOR_BLUE
        
        # State
        self.health = 100
        self.max_health = 100
        self.is_alive = True
        
        # Animation
        self.animation_frame = 0
    
    def update_from_server(self, data: dict):
        """Update player state from server data."""
        self.x = data.get("x", self.x)
        self.y = data.get("y", self.y)
        self.rotation = data.get("rotation", self.rotation)
        self.health = data.get("health", self.health)
        self.max_health = data.get("max_health", self.max_health)
        self.is_alive = data.get("is_alive", self.is_alive)
    
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Render the player on screen."""
        if not self.is_alive:
            return
        
        # Calculate screen position (world pos - camera offset)
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Draw player rectangle
        rect = pygame.Rect(
            screen_x - self.width // 2,
            screen_y - self.height // 2,
            self.width,
            self.height
        )
        pygame.draw.rect(screen, self.color, rect)
        
        # Draw health bar
        self._draw_health_bar(screen, screen_x, screen_y)
        
        # Draw username
        self._draw_username(screen, screen_x, screen_y)
    
    def _draw_health_bar(self, screen: pygame.Surface, x: int, y: int):
        """Draw health bar above player."""
        bar_width = self.width
        bar_height = 5
        bar_y = y - self.height // 2 - 10
        
        # Background (red)
        bg_rect = pygame.Rect(x - bar_width // 2, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, COLOR_RED, bg_rect)
        
        # Health (green)
        health_ratio = self.health / self.max_health
        health_width = int(bar_width * health_ratio)
        health_rect = pygame.Rect(x - bar_width // 2, bar_y, health_width, bar_height)
        pygame.draw.rect(screen, COLOR_GREEN, health_rect)
    
    def _draw_username(self, screen: pygame.Surface, x: int, y: int):
        """Draw username below player."""
        font = pygame.font.Font(None, 20)
        text = font.render(self.username, True, (255, 255, 255))
        text_rect = text.get_rect(center=(x, y + self.height // 2 + 15))
        screen.blit(text, text_rect)
    
    def __repr__(self):
        return f"Player({self.player_id}, '{self.username}', pos=({self.x:.1f}, {self.y:.1f}))"