# client/ui/ui_manager.py
"""
UI Manager
Manages UI screens and navigation between them.
"""

import pygame
from typing import Dict, Optional


class UIScreen:
    """Base class for UI screens."""
    
    def __init__(self, manager):
        self.manager = manager
        self.is_active = False
    
    def on_enter(self):
        """Called when screen becomes active."""
        self.is_active = True
    
    def on_exit(self):
        """Called when screen becomes inactive."""
        self.is_active = False
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame events."""
        pass
    
    def update(self, delta_time: float):
        """Update screen logic."""
        pass
    
    def render(self, screen: pygame.Surface):
        """Render the screen."""
        pass


class UIManager:
    """Manages UI screens and navigation."""
    
    def __init__(self, game):
        self.game = game
        self.screens: Dict[str, UIScreen] = {}
        self.current_screen: Optional[UIScreen] = None
        self.current_screen_name: Optional[str] = None
    
    def add_screen(self, name: str, screen: UIScreen):
        """Add a screen to the manager."""
        self.screens[name] = screen
    
    def switch_to(self, screen_name: str):
        """Switch to a different screen."""
        if screen_name not in self.screens:
            print(f"[UI] Screen '{screen_name}' not found")
            return
        
        # Exit current screen
        if self.current_screen:
            self.current_screen.on_exit()
        
        # Enter new screen
        self.current_screen = self.screens[screen_name]
        self.current_screen_name = screen_name
        self.current_screen.on_enter()
        
        print(f"[UI] Switched to screen: {screen_name}")
    
    def handle_event(self, event: pygame.event.Event):
        """Forward events to current screen."""
        if self.current_screen:
            self.current_screen.handle_event(event)
    
    def update(self, delta_time: float):
        """Update current screen."""
        if self.current_screen:
            self.current_screen.update(delta_time)
    
    def render(self, screen: pygame.Surface):
        """Render current screen."""
        if self.current_screen:
            self.current_screen.render(screen)


class Button:
    """Simple button widget for UI."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        
        # Colors
        self.color_normal = (70, 130, 180)
        self.color_hover = (100, 149, 237)
        self.color_text = (255, 255, 255)
        
        # State
        self.is_hovered = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events. Returns True if button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.callback:
                    self.callback()
                return True
        
        return False
    
    def render(self, screen: pygame.Surface):
        """Render the button."""
        color = self.color_hover if self.is_hovered else self.color_normal
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, width=2, border_radius=5)
        
        # Render text
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, self.color_text)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class InputBox:
    """Text input box widget."""
    
    def __init__(self, x: int, y: int, width: int, height: int, placeholder: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.is_active = False
        self.is_password = False
        
        # Colors
        self.color_inactive = (100, 100, 100)
        self.color_active = (70, 130, 180)
        self.color_text = (255, 255, 255)
        self.color_placeholder = (150, 150, 150)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.is_active = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.KEYDOWN and self.is_active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.is_active = False
            elif len(self.text) < 30:  # Max length
                self.text += event.unicode
    
    def render(self, screen: pygame.Surface):
        """Render the input box."""
        color = self.color_active if self.is_active else self.color_inactive
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, width=2, border_radius=5)
        
        # Render text
        font = pygame.font.Font(None, 32)
        
        if self.text:
            display_text = "*" * len(self.text) if self.is_password else self.text
            text_surface = font.render(display_text, True, self.color_text)
        elif not self.is_active:
            text_surface = font.render(self.placeholder, True, self.color_placeholder)
        else:
            text_surface = font.render("", True, self.color_text)
        
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        screen.blit(text_surface, text_rect)