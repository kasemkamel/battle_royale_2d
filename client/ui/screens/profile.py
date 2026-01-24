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
        
        # Enable scrolling for profile
        self.scrollable = True
        self.scroll_start_y = 150
        
        # Back button
        self.back_button = Button(
            20, SCREEN_HEIGHT - 70, 120, 50, "Back", self.go_back
        )
        
        # Logout button
        self.logout_button = Button(
            SCREEN_WIDTH - 140, SCREEN_HEIGHT - 70, 120, 50, "Logout", self.logout
        )
        
        # Estimate content height (will adjust based on actual stats)
        self.set_content_height(600)
    
    def go_back(self):
        """Navigate back to lobby."""
        self.manager.switch_to("lobby")
    
    def logout(self):
        """Logout and disconnect."""
        self.manager.game.logout()
        self.manager.switch_to("home")
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        super().handle_event(event)
        self.back_button.handle_event(event)
        self.logout_button.handle_event(event)
    
    def render(self, screen: pygame.Surface):
        """Render the profile screen."""
        screen.fill(UI_BG_COLOR)
        
        # Title (fixed)
        title_font = pygame.font.Font(None, 64)
        title_surface = title_font.render("PROFILE", True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Begin scrollable region
        self.begin_scrollable_region(screen)
        
        # Render scrollable content
        self._render_profile_content(screen)
        
        # End scrollable region
        self.end_scrollable_region(screen)
        
        # Buttons (fixed)
        self.back_button.render(screen)
        self.logout_button.render(screen)
    
    def _render_profile_content(self, screen: pygame.Surface):
        """Render scrollable profile content."""
        y_offset = self.get_scrolled_y(180)
        font = pygame.font.Font(None, 36)
        
        game_state = self.manager.game.game_state.get_state_dict()
        
        if game_state.get("user_id"):
            # Username
            if self.is_visible(y_offset):
                username_text = f"Username: {game_state.get('username', 'N/A')}"
                self._draw_centered_text(screen, username_text, font, (255, 255, 255), y_offset)
            y_offset += 50
            
            # User ID
            if self.is_visible(y_offset):
                id_text = f"User ID: {game_state.get('user_id')}"
                self._draw_centered_text(screen, id_text, font, (200, 200, 200), y_offset)
            y_offset += 80
            
            # Stats title
            if self.is_visible(y_offset):
                stats_title = font.render("STATISTICS", True, (255, 215, 0))
                stats_rect = stats_title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(stats_title, stats_rect)
            y_offset += 60
            
            # Display stats
            stats = game_state.get('stats', {})
            stat_items = [
                ("Matches Played", stats.get('matches_played', 0)),
                ("Wins", stats.get('wins', 0)),
                ("Kills", stats.get('kills', 0)),
                ("Deaths", stats.get('deaths', 0)),
                ("K/D Ratio", f"{stats.get('kills', 0) / max(1, stats.get('deaths', 1)):.2f}"),
            ]
            
            for label, value in stat_items:
                if self.is_visible(y_offset):
                    text = f"{label}: {value}"
                    self._draw_centered_text(screen, text, font, (255, 255, 255), y_offset)
                y_offset += 45
        else:
            # Not logged in
            if self.is_visible(y_offset):
                not_logged_in = font.render("Not logged in", True, (255, 100, 100))
                not_logged_rect = not_logged_in.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(not_logged_in, not_logged_rect)
    
    def _draw_centered_text(self, screen, text, font, color, y):
        """Helper to draw centered text."""
        surface = font.render(str(text), True, color)
        rect = surface.get_rect(center=(SCREEN_WIDTH // 2, y))
        screen.blit(surface, rect)