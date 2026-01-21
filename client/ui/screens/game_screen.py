# client/ui/screens/game_screen.py
"""
Game Screen
Main gameplay screen with rendering and HUD.
"""

import pygame
from client.ui.ui_manager import UIScreen
from client.models.player import Player
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_RED, COLOR_GREEN, COLOR_YELLOW


class GameScreen(UIScreen):
    """In-game screen with gameplay and HUD."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Game objects
        self.players = {}  # player_id -> Player
        self.local_player_id = None
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # Zone
        self.zone_center_x = 0
        self.zone_center_y = 0
        self.zone_radius = 0
        self.zone_shrinking = False
        
        # Input state
        self.keys_pressed = set()
        self.mouse_world_x = 0  # Mouse position in world coordinates
        self.mouse_world_y = 0
        self.mouse_screen_x = 0  # Mouse position in screen coordinates
        self.mouse_screen_y = 0
    
    def on_enter(self):
        """Called when entering game screen."""
        super().on_enter()
        print("[GameScreen] Entered game screen")
    
    def update_world_state(self, data: dict):
        """Update game state from server."""
        # Update players
        player_data_list = data.get("players", [])
        
        # Track which players are still in the game
        current_player_ids = set()
        
        for player_data in player_data_list:
            player_id = player_data.get("player_id")
            current_player_ids.add(player_id)
            
            if player_id not in self.players:
                # Create new player
                self.players[player_id] = Player(
                    player_id,
                    player_data.get("username", "Unknown"),
                    player_data.get("x", 0),
                    player_data.get("y", 0)
                )
            
            # Update player
            self.players[player_id].update_from_server(player_data)
        
        # Remove disconnected players
        for player_id in list(self.players.keys()):
            if player_id not in current_player_ids:
                del self.players[player_id]
        
        # Update zone
        zone_data = data.get("zone", {})
        self.zone_center_x = zone_data.get("center_x", 0)
        self.zone_center_y = zone_data.get("center_y", 0)
        self.zone_radius = zone_data.get("radius", 0)
        self.zone_shrinking = zone_data.get("shrinking", False)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)
        elif event.type == pygame.MOUSEMOTION:
            # Track mouse position
            self.mouse_screen_x, self.mouse_screen_y = event.pos
            # Convert to world coordinates
            self.mouse_world_x = self.mouse_screen_x + self.camera_x
            self.mouse_world_y = self.mouse_screen_y + self.camera_y
    
    def update(self, delta_time: float):
        """Update game logic."""
        # Get current mouse position (in case no motion event)
        mouse_pos = pygame.mouse.get_pos()
        self.mouse_screen_x, self.mouse_screen_y = mouse_pos
        self.mouse_world_x = self.mouse_screen_x + self.camera_x
        self.mouse_world_y = self.mouse_screen_y + self.camera_y
        
        # Calculate movement input
        move_x = 0
        move_y = 0
        
        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            move_y -= 1
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            move_y += 1
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            move_x -= 1
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            move_x += 1
        
        # Normalize diagonal movement
        if move_x != 0 and move_y != 0:
            move_x *= 0.707  # 1/sqrt(2)
            move_y *= 0.707
        
        # Check for sprint (Shift key)
        is_sprinting = pygame.K_LSHIFT in self.keys_pressed or pygame.K_RSHIFT in self.keys_pressed
        
        # Check for dash (Spacebar)
        is_dashing = pygame.K_SPACE in self.keys_pressed
        
        # Build actions dict
        actions = {
            "sprint": is_sprinting,
            "dash": is_dashing
        }
        
        # Send input to server (include mouse position)
        #if move_x != 0 or move_y != 0 or is_sprinting or is_dashing:
        self.manager.game.network.send_player_input(
                move_x, move_y, 
                self.mouse_world_x, self.mouse_world_y,
                actions
            )
        
        # Update camera to follow local player
        if self.local_player_id and self.local_player_id in self.players:
            local_player = self.players[self.local_player_id]
            self.camera_x = local_player.x - SCREEN_WIDTH // 2
            self.camera_y = local_player.y - SCREEN_HEIGHT // 2
    
    def render(self, screen: pygame.Surface):
        """Render the game screen."""
        screen.fill(COLOR_BLACK)
        
        # Draw zone (safe area)
        self._draw_zone(screen)
        
        # Draw all players
        for player in self.players.values():
            player.render(screen, self.camera_x, self.camera_y)
        
        # Draw crosshair at mouse position
        self._draw_crosshair(screen)
        
        # Draw HUD
        self._draw_hud(screen)
    
    def _draw_zone(self, screen: pygame.Surface):
        """Draw the safe zone circle."""
        if self.zone_radius <= 0:
            return
        
        # Calculate screen position
        zone_screen_x = int(self.zone_center_x - self.camera_x)
        zone_screen_y = int(self.zone_center_y - self.camera_y)
        
        # Draw zone circle (semi-transparent would be better, but using outline for simplicity)
        try:
            pygame.draw.circle(
                screen,
                (100, 100, 255),
                (zone_screen_x, zone_screen_y),
                int(self.zone_radius),
                3  # Width (outline only)
            )
        except:
            pass  # Ignore if circle is off-screen
    
    def _draw_crosshair(self, screen: pygame.Surface):
        """Draw crosshair at mouse position."""
        x, y = self.mouse_screen_x, self.mouse_screen_y
        size = 10
        thickness = 2
        
        # Draw cross
        pygame.draw.line(screen, COLOR_WHITE, (x - size, y), (x + size, y), thickness)
        pygame.draw.line(screen, COLOR_WHITE, (x, y - size), (x, y + size), thickness)
        
        # Draw circle
        pygame.draw.circle(screen, COLOR_WHITE, (x, y), size, 1)
    
    def _draw_hud(self, screen: pygame.Surface):
        """Draw heads-up display."""
        font = pygame.font.Font(None, 28)
        
        # Player count
        alive_count = sum(1 for p in self.players.values() if p.is_alive)
        player_text = f"Players Alive: {alive_count}"
        player_surface = font.render(player_text, True, COLOR_WHITE)
        screen.blit(player_surface, (10, 10))
        
        # Local player health (if available)
        if self.local_player_id and self.local_player_id in self.players:
            local_player = self.players[self.local_player_id]
            health_text = f"Health: {int(local_player.health)}/{int(local_player.max_health)}"
            health_surface = font.render(health_text, True, (0, 255, 0))
            screen.blit(health_surface, (10, 40))
            
            # Mana
            mana_text = f"Mana: {int(local_player.mana)}/{int(local_player.max_mana)}"
            mana_surface = font.render(mana_text, True, (0, 200, 255))
            screen.blit(mana_surface, (10, 70))
            
            # Sprint indicator
            if local_player.is_sprinting:
                sprint_text = "SPRINTING"
                sprint_surface = font.render(sprint_text, True, COLOR_YELLOW)
                screen.blit(sprint_surface, (10, 100))
        
        # Zone status
        if self.zone_shrinking:
            zone_text = "⚠ ZONE SHRINKING ⚠"
            zone_surface = font.render(zone_text, True, (255, 100, 100))
            zone_rect = zone_surface.get_rect(center=(SCREEN_WIDTH // 2, 20))
            screen.blit(zone_surface, zone_rect)
        else:
            zone_text = "Safe Zone Active"
            zone_surface = font.render(zone_text, True, (100, 255, 100))
            zone_rect = zone_surface.get_rect(center=(SCREEN_WIDTH // 2, 20))
            screen.blit(zone_surface, zone_rect)
        
        # Instructions
        instruction_font = pygame.font.Font(None, 20)
        instructions = "WASD: Move | Shift: Sprint | Space: Dash | ESC: Menu"
        instruction_surface = instruction_font.render(instructions, True, (150, 150, 150))
        screen.blit(instruction_surface, (10, SCREEN_HEIGHT - 30))