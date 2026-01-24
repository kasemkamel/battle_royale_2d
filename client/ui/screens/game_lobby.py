# client/ui/screens/game_lobby.py
# -*- coding: utf-8 -*-
"""
Game Lobby Screen
Pre-game lobby with player list and start game button.
"""

import pygame
from client.ui.ui_manager import UIScreen, Button
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG_COLOR



class GameLobbyScreen(UIScreen):
    """Pre-game lobby screen."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Back button
        self.back_button = Button(
            20, SCREEN_HEIGHT - 70, 120, 50, "Leave", self.leave_lobby
        )
        
        # Skills button
        self.skills_button = Button(
            150, SCREEN_HEIGHT - 70, 120, 50, "Skills", self.go_to_skills
        )
        
        # Profile button
        self.profile_button = Button(
            280, SCREEN_HEIGHT - 70, 120, 50, "Profile", self.go_to_profile
        )
        # Settings button image
        gear_img = pygame.image.load("assets/ui/gear.png").convert_alpha()
        gear_img = pygame.transform.smoothscale(gear_img, (32, 32))
        # Settings button
        self.settings_button = Button(
            SCREEN_WIDTH - 80, 20, 60, 50,"", image = gear_img, callback= self.go_to_settings
        )
        
        # Ready/Start button
        self.ready_button = Button(
            SCREEN_WIDTH - 240, SCREEN_HEIGHT - 70, 220, 50, "Ready", self.toggle_ready
        )
        
        # State
        self.is_ready = False
        self.lobby_players = []
        self.match_starting = False
        self.countdown = 0
    
    def on_enter(self):
        """Called when entering lobby screen."""
        super().on_enter()
        
        # Reset ready state and button text
        self.is_ready = False
        self.ready_button.text = "Ready"
        
        # Join lobby only if we don't have a player_id yet
        if self.manager.game.game_state.user_id and not self.manager.game.game_state.player_id:
            self.manager.game.network.send_join_lobby()
            print("[Lobby] Sent join lobby request")
    
    def leave_lobby(self):
        """Leave the lobby."""
        from shared.packets import Packet
        from shared.enums import PacketType
        
        self.manager.game.network.send(Packet(PacketType.LEAVE_LOBBY))
        self.manager.switch_to("home")
    
    def go_to_skills(self):
        """Navigate to skill selection screen."""
        self.manager.switch_to("skills")
    
    def go_to_profile(self):
        """Navigate to profile screen."""
        self.manager.switch_to("profile")
    
    def go_to_settings(self):
        """Navigate to settings screen."""
        self.manager.switch_to("settings")
    
    def toggle_ready(self):
        """Toggle ready status."""
        self.is_ready = not self.is_ready
        self.manager.game.network.send_player_ready(self.is_ready)
        
        # Update button text
        self.ready_button.text = "Not Ready" if self.is_ready else "Ready"
    
    def update_lobby_state(self, data: dict):
        """Update lobby state from server."""
        self.lobby_players = data.get("players", [])
        self.match_starting = data.get("match_starting", False)
        self.countdown = data.get("countdown", 0)
        
        # Sync our ready state with server
        our_player_id = self.manager.game.game_state.player_id
        if our_player_id:
            for player in self.lobby_players:
                if player.get("player_id") == our_player_id:
                    server_ready = player.get("ready", False)
                    if server_ready != self.is_ready:
                        self.is_ready = server_ready
                        self.ready_button.text = "Not Ready" if self.is_ready else "Ready"
                    break
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        self.back_button.handle_event(event)
        self.skills_button.handle_event(event)
        self.profile_button.handle_event(event)
        self.settings_button.handle_event(event)
        self.ready_button.handle_event(event)
    
    def render(self, screen: pygame.Surface):
        """Render the lobby screen."""
        screen.fill(UI_BG_COLOR)
        
        # Title
        title_font = pygame.font.Font(None, 64)
        title_surface = title_font.render("GAME LOBBY", True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Match starting countdown
        if self.match_starting:
            countdown_font = pygame.font.Font(None, 48)
            countdown_text = f"Match starting in {self.countdown}..."
            countdown_surface = countdown_font.render(countdown_text, True, (255, 100, 100))
            countdown_rect = countdown_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
            screen.blit(countdown_surface, countdown_rect)
            y_start = 220
        else:
            y_start = 180
        
        # Player list header
        header_font = pygame.font.Font(None, 40)
        header_surface = header_font.render(f"Players ({len(self.lobby_players)})", True, (200, 200, 200))
        header_rect = header_surface.get_rect(center=(SCREEN_WIDTH // 2, y_start))
        screen.blit(header_surface, header_rect)
        
        # Player list
        player_font = pygame.font.Font(None, 32)
        y_offset = y_start + 60
        
        for player in self.lobby_players:
            # Player name
            name = player.get("username", "Unknown")
            ready = player.get("ready", False)
            
            # Color based on ready status
            color = (0, 255, 0) if ready else (255, 255, 255)
            status = " ✓" if ready else ""
            
            player_text = f"{name}{status}"
            player_surface = player_font.render(player_text, True, color)
            player_rect = player_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(player_surface, player_rect)
            
            y_offset += 40
        
        # Instructions
        if not self.lobby_players:
            instruction_font = pygame.font.Font(None, 28)
            instruction = "Waiting for players to join..."
            instruction_surface = instruction_font.render(instruction, True, (150, 150, 150))
            instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, 300))
            screen.blit(instruction_surface, instruction_rect)
        
        # Buttons
        self.back_button.render(screen)
        self.skills_button.render(screen)
        self.profile_button.render(screen)
        self.settings_button.render(screen)
        self.ready_button.render(screen)
        
        # Ready status
        status_font = pygame.font.Font(None, 24)
        status_text = "You are ready!" if self.is_ready else "Click Ready when you're ready"
        status_color = (0, 255, 0) if self.is_ready else (200, 200, 200)
        status_surface = status_font.render(status_text, True, status_color)
        status_rect = status_surface.get_rect(midright=(SCREEN_WIDTH - 260, SCREEN_HEIGHT - 95))
        screen.blit(status_surface, status_rect)