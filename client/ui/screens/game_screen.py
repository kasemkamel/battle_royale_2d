# client/ui/screens/game_screen.py
"""
Game Screen
Main gameplay screen with rendering and HUD.
"""

import pygame
from client.ui.ui_manager import UIScreen
from client.models.player import Player
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_RED


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
        
        # Input state
        self.keys_pressed = set()
    
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
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)
    
    def update(self, delta_time: float):
        """Update game logic."""
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
        
        # Send input to server
        if move_x != 0 or move_y != 0:
            self.manager.game.network.send_player_input(move_x, move_y)
        
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
        
        # Instructions
        instruction_font = pygame.font.Font(None, 20)
        instructions = "WASD: Move | ESC: Menu"
        instruction_surface = instruction_font.render(instructions, True, (150, 150, 150))
        screen.blit(instruction_surface, (10, SCREEN_HEIGHT - 30))