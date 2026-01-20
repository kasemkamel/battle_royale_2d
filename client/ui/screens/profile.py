"""
Profile Screen
Displays player stats, achievements, and account information.
"""

import pygame
from client.ui.ui_manager import UIScreen, Button
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG_COLOR


class ProfileScreen(UIScreen):
    """Player profile and statistics screen."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Back button
        self.back_button = Button(
            20, SCREEN_HEIGHT - 70, 120, 50, "Back", self.go_back
        )
        
        # Logout button
        self.logout_button = Button(
            SCREEN_WIDTH - 140, SCREEN_HEIGHT - 70, 120, 50, "Logout", self.logout
        )
    
    def go_back(self):
        """Navigate back to home."""
        self.manager.switch_to("lobby")
    
    def logout(self):
        """Logout and disconnect."""
        self.manager.game.logout()
        self.manager.switch_to("home")
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        self.back_button.handle_event(event)
        self.logout_button.handle_event(event)
    
    def render(self, screen: pygame.Surface):
        """Render the profile screen."""
        screen.fill(UI_BG_COLOR)
        
        # Title
        title_font = pygame.font.Font(None, 64)
        title_surface = title_font.render("PROFILE", True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Get game state
        game_state = self.manager.game.game_state.get_state_dict()
        
        # Display user info
        y_offset = 180
        font = pygame.font.Font(None, 36)
        
        if game_state.get("user_id"):
            # Username
            username_text = f"Username: {game_state.get('username', 'N/A')}"
            self._draw_text(screen, username_text, font, (255, 255, 255), SCREEN_WIDTH // 2, y_offset)
            y_offset += 50
            
            # User ID
            id_text = f"User ID: {game_state.get('user_id')}"
            self._draw_text(screen, id_text, font, (200, 200, 200), SCREEN_WIDTH // 2, y_offset)
            y_offset += 80
            
            # Stats
            stats = game_state.get('stats', {})
            
            stats_title = font.render("STATISTICS", True, (255, 215, 0))
            stats_rect = stats_title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(stats_title, stats_rect)
            y_offset += 60
            
            # Display stats
            stat_items = [
                ("Matches Played", stats.get('matches_played', 0)),
                ("Wins", stats.get('wins', 0)),
                ("Kills", stats.get('kills', 0)),
                ("Deaths", stats.get('deaths', 0)),
                ("K/D Ratio", f"{stats.get('kills', 0) / max(1, stats.get('deaths', 1)):.2f}"),
            ]
            
            for label, value in stat_items:
                text = f"{label}: {value}"
                self._draw_text(screen, text, font, (255, 255, 255), SCREEN_WIDTH // 2, y_offset)
                y_offset += 45
        else:
            # Not logged in
            not_logged_in = font.render("Not logged in", True, (255, 100, 100))
            not_logged_rect = not_logged_in.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(not_logged_in, not_logged_rect)
        
        # Buttons
        self.back_button.render(screen)
        self.logout_button.render(screen)
    
    def _draw_text(self, screen, text, font, color, x, y):
        """Helper to draw centered text."""
        surface = font.render(str(text), True, color)
        rect = surface.get_rect(center=(x, y))
        screen.blit(surface, rect)