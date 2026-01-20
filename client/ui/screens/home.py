# client\ui\screens\home.py
"""
Home Screen
Main landing page with login/register functionality.
"""

import pygame
from client.ui.ui_manager import UIScreen, Button, InputBox
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG_COLOR


class HomeScreen(UIScreen):
    """Home/login screen."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # UI elements
        center_x = SCREEN_WIDTH // 2
        
        # Title
        self.title = "2D BATTLE ROYALE"
        
        # Input boxes
        self.username_input = InputBox(
            center_x - 150, 250, 300, 50, "Username"
        )
        self.password_input = InputBox(
            center_x - 150, 320, 300, 50, "Password"
        )
        self.password_input.is_password = True
        
        # Buttons
        self.login_button = Button(
            center_x - 150, 400, 140, 50, "Login", self.on_login
        )
        self.register_button = Button(
            center_x + 10, 400, 140, 50, "Register", self.on_register
        )
        
        
        # Status message
        self.status_message = ""
        self.status_color = (255, 255, 255)
    
    def on_enter(self):
        """Called when entering this screen."""
        super().on_enter()
        self.status_message = ""
        
        # Try to connect to server
        if not self.manager.game.network.is_connected:
            self.manager.game.connect_to_server()
    
    def on_login(self):
        """Handle login button click."""
        username = self.username_input.text.strip()
        password = self.password_input.text
        
        if not username or not password:
            self.show_status("Please enter username and password", (255, 100, 100))
            return
        
        # Send login request
        self.manager.game.network.send_login(username, password)
        self.show_status("Logging in...", (255, 255, 100))
    
    def on_register(self):
        """Handle register button click."""
        username = self.username_input.text.strip()
        password = self.password_input.text
        
        if not username or not password:
            self.show_status("Please enter username and password", (255, 100, 100))
            return
        
        if len(username) < 3:
            self.show_status("Username must be at least 3 characters", (255, 100, 100))
            return
        
        if len(password) < 6:
            self.show_status("Password must be at least 6 characters", (255, 100, 100))
            return
        
        # Send register request
        self.manager.game.network.send_register(username, password)
        self.show_status("Registering...", (255, 255, 100))

    
    def show_status(self, message: str, color: tuple = (255, 255, 255)):
        """Show status message."""
        self.status_message = message
        self.status_color = color
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        self.username_input.handle_event(event)
        self.password_input.handle_event(event)
        self.login_button.handle_event(event)
        self.register_button.handle_event(event)
        
    
    def render(self, screen: pygame.Surface):
        """Render the home screen."""
        screen.fill(UI_BG_COLOR)
        
        # Title
        title_font = pygame.font.Font(None, 72)
        title_surface = title_font.render(self.title, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)
        
        # Input boxes
        self.username_input.render(screen)
        self.password_input.render(screen)
        
        # Buttons
        self.login_button.render(screen)
        self.register_button.render(screen)
        
        
        # Status message
        if self.status_message:
            status_font = pygame.font.Font(None, 28)
            status_surface = status_font.render(self.status_message, True, self.status_color)
            status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, 480))
            screen.blit(status_surface, status_rect)
        
        # Connection status
        conn_status = "Connected" if self.manager.game.network.is_connected else "Disconnected"
        conn_color = (0, 255, 0) if self.manager.game.network.is_connected else (255, 0, 0)
        conn_font = pygame.font.Font(None, 24)
        conn_surface = conn_font.render(f"Server: {conn_status}", True, conn_color)
        screen.blit(conn_surface, (20, 20))