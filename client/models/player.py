# client/models/player.py
"""
Player Model (Client)
Client-side representation of a player for rendering and display.
"""

import pygame
import math
from shared.constants import PLAYER_WIDTH, PLAYER_HEIGHT, COLOR_BLUE, COLOR_RED, COLOR_GREEN, COLOR_WHITE, COLOR_YELLOW


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
        self.mana = 100
        self.max_mana = 100
        self.is_alive = True
        self.is_sprinting = False
        self.is_dashing = False
        self.is_stunned = False
        
        # Animation
        self.animation_frame = 0
    
    def update_from_server(self, data: dict):
        """Update player state from server data."""
        self.x = data.get("x", self.x)
        self.y = data.get("y", self.y)
        self.rotation = data.get("rotation", self.rotation)
        self.health = data.get("health", self.health)
        self.max_health = data.get("max_health", self.max_health)
        self.mana = data.get("mana", self.mana)
        self.max_mana = data.get("max_mana", self.max_mana)
        self.is_alive = data.get("is_alive", self.is_alive)
        self.is_sprinting = data.get("is_sprinting", False)
        self.is_dashing = data.get("is_dashing", False)
        self.is_stunned = data.get("is_stunned", False)
    
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Render the player on screen."""
        if not self.is_alive:
            return
        
        # Calculate screen position (world pos - camera offset)
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Draw player as rotated triangle (pointing toward mouse)
        self._draw_rotated_player(screen, screen_x, screen_y)
        
        # Draw effects
        if self.is_dashing:
            self._draw_dash_trail(screen, screen_x, screen_y)
        if self.is_stunned:
            self._draw_stun_indicator(screen, screen_x, screen_y)
        
        # Draw health bar
        self._draw_health_bar(screen, screen_x, screen_y)
        
        # Draw mana bar
        self._draw_mana_bar(screen, screen_x, screen_y)
        
        # Draw username
        self._draw_username(screen, screen_x, screen_y)
    
    def _draw_rotated_player(self, screen: pygame.Surface, x: int, y: int):
        """Draw player as circle with direction line."""
        radius = self.width // 2
        
        # Choose color based on state
        if self.is_dashing:
            color = COLOR_YELLOW
        elif self.is_stunned:
            color = (128, 128, 128)  # Gray when stunned
        else:
            color = self.color
        
        # Draw circle body
        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, COLOR_WHITE, (x, y), radius, 2)  # Outline
        
        # Draw direction line from center to edge
        line_length = radius
        end_x = x + math.cos(self.rotation) * line_length
        end_y = y + math.sin(self.rotation) * line_length
        pygame.draw.line(screen, COLOR_WHITE, (x, y), (end_x, end_y), 3)
    
    def _draw_dash_trail(self, screen: pygame.Surface, x: int, y: int):
        """Draw dash effect."""
        # Draw circle around player
        pygame.draw.circle(screen, COLOR_YELLOW, (x, y), self.width, 2)
    
    def _draw_stun_indicator(self, screen: pygame.Surface, x: int, y: int):
        """Draw stun stars above player."""
        star_y = y - self.height
        font = pygame.font.Font(None, 30)
        text = font.render("★★★", True, COLOR_YELLOW)
        text_rect = text.get_rect(center=(x, star_y))
        screen.blit(text, text_rect)
    
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
    
    def _draw_mana_bar(self, screen: pygame.Surface, x: int, y: int):
            """Draw mana bar above health bar."""
            bar_width = self.width
            bar_height = 4
            bar_y = y - self.height // 2 - 20
            
            # Background (dark blue)
            bg_rect = pygame.Rect(x - bar_width // 2, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, (0, 0, 100), bg_rect)
            
            # Mana (cyan)
            mana_ratio = self.mana / self.max_mana
            mana_width = int(bar_width * mana_ratio)
            mana_rect = pygame.Rect(x - bar_width // 2, bar_y, mana_width, bar_height)
            pygame.draw.rect(screen, (0, 200, 255), mana_rect)

    def _draw_username(self, screen: pygame.Surface, x: int, y: int):
        """Draw username below player."""
        font = pygame.font.Font(None, 20)
        text = font.render(self.username, True, (255, 255, 255))
        text_rect = text.get_rect(center=(x, y + self.height // 2 + 15))
        screen.blit(text, text_rect)
    
    def __repr__(self):
        return f"Player({self.player_id}, '{self.username}', pos=({self.x:.1f}, {self.y:.1f}))"

