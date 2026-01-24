# client/core/game.py
"""
Game Client
Main game client orchestrating all client subsystems.
"""

import pygame
import sys
from client.network.client import NetworkClient
from client.core.game_state import ClientGameState
from client.ui.ui_manager import UIManager
from client.ui.screens.home import HomeScreen
from client.ui.screens.profile import ProfileScreen
from client.ui.screens.settings import SettingsScreen
from client.ui.screens.game_lobby import GameLobbyScreen
from client.ui.screens.game_screen import GameScreen
from client.ui.screens.skill_select import SkillSelectionScreen
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE
from shared.enums import PacketType


class Game:
    """Main game client."""
    
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Create window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        self.is_running = False
        
        # Game state
        self.game_state = ClientGameState()
        
        # Network client
        self.network = NetworkClient()
        self.network.set_packet_callback(self.on_packet_received)
        self.network.set_connection_callback(self.on_connection_changed)
        
        # UI Manager
        self.ui_manager = UIManager(self)
        
        # Create and add screens
        self.home_screen = HomeScreen(self.ui_manager)
        self.profile_screen = ProfileScreen(self.ui_manager)
        self.settings_screen = SettingsScreen(self.ui_manager)
        self.lobby_screen = GameLobbyScreen(self.ui_manager)
        self.game_screen = GameScreen(self.ui_manager)
        self.skill_select_screen = SkillSelectionScreen(self.ui_manager)
        
        self.ui_manager.add_screen("home", self.home_screen)
        self.ui_manager.add_screen("profile", self.profile_screen)
        self.ui_manager.add_screen("settings", self.settings_screen)
        self.ui_manager.add_screen("lobby", self.lobby_screen)
        self.ui_manager.add_screen("game", self.game_screen)
        self.ui_manager.add_screen("skills", self.skill_select_screen)
        
        # Start on home screen
        self.ui_manager.switch_to("home")
        
        print("[Game] Client initialized")
    
    def connect_to_server(self):
        """Connect to game server."""
        self.network.connect()
    
    def logout(self):
        """Logout current user."""
        from shared.packets import Packet
        self.network.send(Packet(PacketType.LOGOUT))
        self.game_state.logout()
    
    def on_packet_received(self, packet):
        """Handle received packet from server."""
        handlers = {
            PacketType.LOGIN_RESPONSE: self._handle_login_response,
            PacketType.REGISTER_RESPONSE: self._handle_register_response,
            PacketType.LOBBY_STATE: self._handle_lobby_state,
            PacketType.GAME_START: self._handle_game_start,
            PacketType.WORLD_STATE: self._handle_world_state,
            PacketType.MATCH_END: self._handle_match_end,
            PacketType.ALL_SKILLS_RESPONSE: self._handle_all_skills,
            PacketType.SKILL_LOADOUT_RESPONSE: self._handle_skill_loadout_response,
        }
        
        handler = handlers.get(packet.type)
        if handler:
            handler(packet)
    
    def on_connection_changed(self, connected: bool):
        """Handle connection state change."""
        self.game_state.set_connected(connected)
    
    def _handle_login_response(self, packet):
        """Handle login response from server."""
        success = packet.data.get("success")
        message = packet.data.get("message")
        
        if success:
            user_id = packet.data.get("user_id")
            stats = packet.data.get("stats", {})
            skill_loadout = packet.data.get("skill_loadout", [])
            username = self.home_screen.username_input.text.strip()
            
            self.game_state.login(user_id, username, stats)
            
            # Store skill loadout
            self.game_state.user_data["skill_loadout"] = skill_loadout
            
            print(f"[Game] Login successful - Loadout: {skill_loadout}")
            print(f"[Game] Game state user_data: {self.game_state.user_data}")
            
            self.home_screen.show_status("Login successful!", (0, 255, 0))
            
            # Switch to lobby
            self.ui_manager.switch_to("lobby")
        else:
            self.home_screen.show_status(message, (255, 100, 100))
    
    def _handle_register_response(self, packet):
        """Handle registration response from server."""
        success = packet.data.get("success")
        message = packet.data.get("message")
        
        if success:
            self.home_screen.show_status("Registration successful! Please login.", (0, 255, 0))
        else:
            self.home_screen.show_status(message, (255, 100, 100))
    
    def _handle_lobby_state(self, packet):
        """Handle lobby state update."""
        # Update player_id if we're in the lobby
        players_in_lobby = packet.data.get("players", [])
        if not self.game_state.player_id and self.game_state.user_id:
            # Find our player in the lobby
            for player_data in players_in_lobby:
                if player_data.get("user_id") == self.game_state.user_id:
                    self.game_state.set_player_id(player_data.get("player_id"))
                    break
        
        self.lobby_screen.update_lobby_state(packet.data)
    
    def _handle_game_start(self, packet):
        """Handle game start signal."""
        print("[Game] Match starting!")
        self.ui_manager.switch_to("game")
    
    def _handle_world_state(self, packet):
        """Handle world state update during gameplay."""
        # DEBUG: Print first state received
        if not hasattr(self, '_first_state_received'):
            self._first_state_received = True
            print(f"[DEBUG] First world state received:")
            print(f"  Players: {len(packet.data.get('players', []))}")
            for p in packet.data.get('players', []):
                print(f"    - {p.get('username')}: cooldowns={p.get('skill_cooldowns', 'MISSING')}")
        
        try:
            if self.ui_manager.current_screen_name == "game":
                self.game_screen.update_world_state(packet.data)
                
                if not self.game_screen.local_player_id and self.game_state.player_id:
                    self.game_screen.local_player_id = self.game_state.player_id
        except Exception as e:
            print(f"[Game] ERROR handling world state: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_match_end(self, packet):
        """Handle match end."""
        winner = packet.data.get("winner")
        if winner:
            print(f"[Game] Match ended! Winner: {winner.get('username')}")
        else:
            print("[Game] Match ended! No winner.")
        
        # Reset ready state
        self.lobby_screen.is_ready = False
        self.lobby_screen.ready_button.text = "Ready"
        
        # Return to lobby
        self.ui_manager.switch_to("lobby")
    
    def _handle_all_skills(self, packet):
        """Handle all skills response."""
        skills = packet.data.get("skills", [])
        
        # Send to skill select screen if it's the current screen
        if self.ui_manager.current_screen_name == "skills":
            self.skill_select_screen.receive_all_skills(skills)
        
        # Also send to game screen if in game
        elif self.ui_manager.current_screen_name == "game":
            self.game_screen.receive_skills_data(skills)
    
    def _handle_skill_loadout_response(self, packet):
        """Handle skill loadout save response."""
        success = packet.data.get("success")
        message = packet.data.get("message")
        loadout = packet.data.get("skill_loadout", [])
        
        if success:
            # Update game state with new loadout
            self.game_state.user_data["skill_loadout"] = loadout
            print(f"[Game] Skill loadout updated: {loadout}")
        
        self.skill_select_screen.on_save_response(success, message, loadout)
    
    def run(self):
        """Main game loop."""
        self.is_running = True
        
        while self.is_running:
            # Calculate delta time
            delta_time = self.clock.tick(FPS) / 1000.0  # Convert to seconds
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # ESC key handling (could add pause menu)
                        if self.ui_manager.current_screen_name == "game":
                            self.ui_manager.switch_to("lobby")
                
                # Forward to UI
                self.ui_manager.handle_event(event)
            
            # Update
            self.ui_manager.update(delta_time)
            
            # Render
            self.ui_manager.render(self.screen)
            
            # Update display
            pygame.display.flip()
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("[Game] Shutting down...")
        self.network.disconnect()
        pygame.quit()
        sys.exit()


# Property to access game state as dict
@property
def game_state_dict(self):
    return self.game_state.get_state_dict()

# Game.game_state = property(lambda self: self.game_state.get_state_dict())