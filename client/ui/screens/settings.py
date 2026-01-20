# client\ui\screens\settings.py
"""
Settings Screen
Game settings and information.
"""

import pygame
from client.ui.ui_manager import UIScreen, Button
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG_COLOR, SERVER_HOST, SERVER_PORT


class SettingsScreen(UIScreen):
    """Settings and game information screen."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Back button
        self.back_button = Button(
            20, SCREEN_HEIGHT - 70, 120, 50, "Back", self.go_back
        )
    
    def go_back(self):
        """Navigate back to home."""
        self.manager.switch_to("lobby")
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        self.back_button.handle_event(event)
    
    def render(self, screen: pygame.Surface):
        """Render the settings screen."""
        screen.fill(UI_BG_COLOR)
        
        # Title
        title_font = pygame.font.Font(None, 64)
        title_surface = title_font.render("SETTINGS & INFO", True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Game Info
        y_offset = 180
        font = pygame.font.Font(None, 32)
        
        info_items = [
            ("GAME INFORMATION", None, (255, 215, 0)),
            ("", None, None),
            ("Game Type", "2D Battle Royale", (255, 255, 255)),
            ("Version", "1.0.0 Alpha", (200, 200, 200)),
            ("", None, None),
            ("SERVER SETTINGS", None, (255, 215, 0)),
            ("", None, None),
            ("Server Address", f"{SERVER_HOST}:{SERVER_PORT}", (255, 255, 255)),
            ("Connection", "Active" if self.manager.game.network.is_connected else "Inactive",
             (0, 255, 0) if self.manager.game.network.is_connected else (255, 0, 0)),
            ("", None, None),
            ("CONTROLS", None, (255, 215, 0)),
            ("", None, None),
            ("Movement", "WASD or Arrow Keys", (255, 255, 255)),
            ("Attack", "Left Click", (255, 255, 255)),
            ("Skill 1", "Q", (255, 255, 255)),
            ("Skill 2", "E", (255, 255, 255)),
            ("", None, None),
            ("ABOUT", None, (255, 215, 0)),
            ("", None, None),
            ("", "2D Battle Royale Game", (255, 255, 255)),
            ("", "Built with Python & Pygame", (200, 200, 200)),
            ("", "Senior Python Game Developer", (150, 150, 150)),
        ]
        
        for item in info_items:
            if item[1] is None and item[0]:
                # Section header
                text = font.render(item[0], True, item[2])
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(text, text_rect)
            elif item[0] and item[1]:
                # Key-value pair
                label = font.render(f"{item[0]}:", True, (200, 200, 200))
                value = font.render(str(item[1]), True, item[2])
                
                label_rect = label.get_rect(midright=(SCREEN_WIDTH // 2 - 20, y_offset))
                value_rect = value.get_rect(midleft=(SCREEN_WIDTH // 2 + 20, y_offset))
                
                screen.blit(label, label_rect)
                screen.blit(value, value_rect)
            elif item[1]:
                # Centered text
                text = font.render(item[1], True, item[2])
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(text, text_rect)
            
            y_offset += 35
        
        # Back button
        self.back_button.render(screen)