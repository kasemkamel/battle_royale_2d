# client/ui/screens/game_screen.py

"""
Game Screen
Main gameplay screen with rendering and HUD.
"""

import math
import pygame
from client.ui.ui_manager import UIScreen
from client.models.player import Player
from shared.constants import COLOR_YELLOW, SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_RED
from shared.enums import PacketType
from shared.packets import Packet


class GameScreen(UIScreen):
    """In-game screen with gameplay and HUD."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Game objects
        self.players = {}  # player_id -> Player
        self.local_player_id = None
        
        self.projectiles = []

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
        
        # Skill system
        self.equipped_skills = []  # Player's equipped skills
        self.active_skill_index = None  # Which skill is being aimed (0-3)
    
    def on_enter(self):
        """Called when entering game screen."""
        super().on_enter()
        # Hide mouse cursor during gameplay
        pygame.mouse.set_visible(False)
        
        # Load player's equipped skills
        self._load_equipped_skills()
        
        print("[GameScreen] Entered game screen")
    
    def update_world_state(self, data: dict):
        """Update game state from server."""
        try:
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
            
            # Update projectiles
            self.projectiles = data.get("projectiles", [])
            
            # Update zone
            zone_data = data.get("zone", {})
            self.zone_center_x = zone_data.get("center_x", 0)
            self.zone_center_y = zone_data.get("center_y", 0)
            self.zone_radius = zone_data.get("radius", 0)
            self.zone_shrinking = zone_data.get("shrinking", False)
            
        except Exception as e:
            print(f"[GameScreen] ERROR updating world state: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
            
            # Check for skill casts (release of Q/E/R/F)
            # Skills are cast on key release, not press (allows aiming)
            
        elif event.type == pygame.KEYUP:
            # Cast skill on key release
            if event.key == pygame.K_q:
                self._cast_skill(0)
            elif event.key == pygame.K_e:
                self._cast_skill(1)
            elif event.key == pygame.K_r:
                self._cast_skill(2)
            elif event.key == pygame.K_f:
                self._cast_skill(3)
            
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
        # if move_x != 0 or move_y != 0 or is_sprinting or is_dashing:
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
        self._draw_projectiles(screen)
        # Draw all players
        for player in self.players.values():
            player.render(screen, self.camera_x, self.camera_y)
        
        # Draw skill indicators (on top of players)
        self._draw_skill_indicators(screen)
        
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
    
    def _draw_skill_indicators(self, screen: pygame.Surface):
        """Draw visual indicators for skills being aimed."""
        if not self.local_player_id or self.local_player_id not in self.players:
            return
        
        local_player = self.players[self.local_player_id]
        
        # Get player screen position
        player_screen_x = int(local_player.x - self.camera_x)
        player_screen_y = int(local_player.y - self.camera_y)
        
        # Mouse screen position
        mouse_screen_x = self.mouse_screen_x
        mouse_screen_y = self.mouse_screen_y
        
        # Check which skill is being aimed (Q, E, R, F held)
        skill_index = None
        if pygame.K_q in self.keys_pressed:
            skill_index = 0
        elif pygame.K_e in self.keys_pressed:
            skill_index = 1
        elif pygame.K_r in self.keys_pressed:
            skill_index = 2
        elif pygame.K_f in self.keys_pressed:
            skill_index = 3
        
        if skill_index is not None and skill_index < len(self.equipped_skills):
            skill = self.equipped_skills[skill_index]
            category = skill.get("category", "")
            
            # Different indicators for different skill types
            if category == "SKILLSHOT":
                self._draw_skillshot_indicator(screen, player_screen_x, player_screen_y, 
                                               mouse_screen_x, mouse_screen_y, skill)
            
            elif category == "AOE":
                self._draw_aoe_indicator(screen, mouse_screen_x, mouse_screen_y, skill)
            
            elif category == "RANGEBASED":
                self._draw_rangebased_indicator(screen, player_screen_x, player_screen_y, skill)
            
            elif category == "HOMING":
                self._draw_homing_indicator(screen, player_screen_x, player_screen_y, skill)
            
            elif category == "CHANNELING":
                self._draw_channeling_indicator(screen, player_screen_x, player_screen_y,
                                                mouse_screen_x, mouse_screen_y, skill)
            
            elif category == "DEFENSIVE":
                self._draw_defensive_indicator(screen, player_screen_x, player_screen_y, skill)
            
            elif category == "CROWD_CONTROL":
                self._draw_cc_indicator(screen, mouse_screen_x, mouse_screen_y, skill)
    
    def _draw_skillshot_indicator(self, screen, px, py, mx, my, skill):
        """Draw line indicator for skillshot with FIXED range."""
        width = skill.get("projectile_width", 20)
        max_range = skill.get("max_range", 800)
        
        # Calculate direction to mouse
        dx = mx - px
        dy = my - py
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0:
            # No direction, point right by default
            dx, dy = 1, 0
        else:
            # Normalize direction
            dx /= length
            dy /= length
        
        # Always draw line at FIXED max_range (not variable)
        end_x = px + dx * max_range
        end_y = py + dy * max_range
        
        # Draw range line (always same length)
        pygame.draw.line(screen, (255, 200, 0), (px, py), (int(end_x), int(end_y)), 2)
        
        # Draw circle at end to show where projectile will reach
        pygame.draw.circle(screen, (255, 200, 0), (int(end_x), int(end_y)), int(width), 2)
        
        # Draw projectile preview at mouse cursor (if within range)
        if length <= max_range:
            pygame.draw.circle(screen, (255, 200, 0), (mx, my), int(width / 2), 2)
        else:
            # Draw at max range instead
            pygame.draw.circle(screen, (255, 100, 100), (int(end_x), int(end_y)), int(width / 2), 0)
    
    def _draw_aoe_indicator(self, screen, mx, my, skill):
        """Draw circle indicator for AOE skills."""
        radius = skill.get("radius", 150)
        
        # Outer circle (impact area)
        pygame.draw.circle(screen, (255, 100, 100), (mx, my), int(radius), 3)
        
        # Inner circle (center)
        pygame.draw.circle(screen, (255, 150, 150), (mx, my), 10, 0)
    
    def _draw_rangebased_indicator(self, screen, px, py, skill):
        """Draw circle around player for range-based skills."""
        radius = skill.get("radius", 200)
        
        # Circle around player
        pygame.draw.circle(screen, (100, 200, 255), (px, py), int(radius), 3)
        
        # Pulsing effect (optional)
        pulse_radius = int(radius * 0.8)
        pygame.draw.circle(screen, (100, 200, 255, 100), (px, py), pulse_radius, 1)
    
    def _draw_homing_indicator(self, screen, px, py, skill):
        """Draw indicator for homing skills."""
        max_range = 400  # Homing range
        
        # Circle showing activation range
        pygame.draw.circle(screen, (200, 100, 255), (px, py), int(max_range), 2)
        
        # Draw arrow at player
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = px + math.cos(rad) * 15
            y = py + math.sin(rad) * 15
            pygame.draw.circle(screen, (200, 100, 255), (int(x), int(y)), 3, 0)
    
    def _draw_channeling_indicator(self, screen, px, py, mx, my, skill):
        """Draw beam indicator for channeling skills."""
        max_range = skill.get("max_range", 400)
        beam_width = skill.get("beam_width", 20)
        
        # Calculate direction
        dx = mx - px
        dy = my - py
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Clamp to max range
        actual_range = min(distance, max_range)
        end_x = px + dx * actual_range
        end_y = py + dy * actual_range
        
        # Draw beam outline
        pygame.draw.line(screen, (255, 255, 100), (px, py), (int(end_x), int(end_y)), int(beam_width))
        pygame.draw.line(screen, (255, 255, 0), (px, py), (int(end_x), int(end_y)), int(beam_width / 2))
    
    def _draw_defensive_indicator(self, screen, px, py, skill):
        """Draw shield indicator for defensive skills."""
        # Shield circle around player
        pygame.draw.circle(screen, (0, 255, 200), (px, py), 30, 3)
        pygame.draw.circle(screen, (0, 200, 255), (px, py), 35, 1)
    
    def _draw_cc_indicator(self, screen, mx, my, skill):
        """Draw indicator for crowd control skills."""
        radius = skill.get("radius", 120)
        
        # Purple circle for CC
        pygame.draw.circle(screen, (200, 100, 200), (mx, my), int(radius), 3)
        
        # X pattern inside
        size = 15
        pygame.draw.line(screen, (200, 100, 200), 
                        (mx - size, my - size), (mx + size, my + size), 2)
        pygame.draw.line(screen, (200, 100, 200), 
                        (mx - size, my + size), (mx + size, my - size), 2)
    
    def _load_equipped_skills(self):
        """Load player's equipped skills for display."""
        # Request skills from server or use cached data
        from shared.packets import Packet
        from shared.enums import PacketType
        
        # For now, request all skills to get full data
        self.manager.game.network.send(Packet(PacketType.GET_ALL_SKILLS))
    
    def receive_skills_data(self, all_skills_data: list):
        """Called when skill data is received."""
        # Get player's loadout
        loadout = self.manager.game.game_state.user_data.get("skill_loadout", [])
        
        # Match loadout IDs to full skill data
        self.equipped_skills = []
        for skill_id in loadout:
            skill_data = next((s for s in all_skills_data if s["skill_id"] == skill_id), None)
            if skill_data:
                self.equipped_skills.append(skill_data)
        
        print(f"[GameScreen] Loaded {len(self.equipped_skills)} equipped skills")
    
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
        instructions = "WASD: Move | Shift: Sprint | Space: Dash | Q/E/R/F: Skills | ESC: Menu"
        instruction_surface = instruction_font.render(instructions, True, (150, 150, 150))
        screen.blit(instruction_surface, (10, SCREEN_HEIGHT - 30))
        
        # Skill bar (bottom center)
        self._draw_skill_bar(screen)
    
    def _draw_skill_bar(self, screen: pygame.Surface):
        """Draw skill bar showing equipped skills."""
        if not self.equipped_skills:
            return
        
        bar_width = 400
        bar_height = 80
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT - bar_height - 10
        
        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (30, 30, 40, 200), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100), bg_rect, width=2, border_radius=5)
        
        # Get local player for cooldowns
        local_player = None
        if self.local_player_id and self.local_player_id in self.players:
            local_player = self.players[self.local_player_id]
        
        # Skill slots
        slot_size = 70
        slot_spacing = 10
        keys = ["Q", "E", "R", "F"]
        
        for i in range(4):
            x = bar_x + 15 + i * (slot_size + slot_spacing)
            y = bar_y + 5
            
            # Slot background
            slot_rect = pygame.Rect(x, y, slot_size, slot_size)
            
            if i < len(self.equipped_skills):
                skill = self.equipped_skills[i]
                
                # Get cooldown from server (via local_player)
                cooldown = 0
                if local_player and hasattr(local_player, 'skill_cooldowns') and i < len(local_player.skill_cooldowns):
                    cooldown = local_player.skill_cooldowns[i]
                
                # Determine slot color based on cooldown
                if cooldown > 0:
                    slot_color = (60, 60, 80)  # On cooldown
                else:
                    slot_color = (80, 120, 160)  # Ready
                
                pygame.draw.rect(screen, slot_color, slot_rect, border_radius=3)
                pygame.draw.rect(screen, (150, 150, 150), slot_rect, width=2, border_radius=3)
                
                # Skill name
                name_font = pygame.font.Font(None, 18)
                name_surface = name_font.render(skill["name"][:8], True, (255, 255, 255))
                name_rect = name_surface.get_rect(center=(x + slot_size // 2, y + 15))
                screen.blit(name_surface, name_rect)
                
                # Mana cost
                mana_font = pygame.font.Font(None, 16)
                mana_text = f"{int(skill['mana_cost'])}M"
                mana_surface = mana_font.render(mana_text, True, (100, 200, 255))
                screen.blit(mana_surface, (x + 5, y + slot_size - 20))
                
                # Cooldown overlay
                if cooldown > 0:
                    # Dark overlay
                    overlay = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, (x, y))
                    
                    # Cooldown text
                    cd_font = pygame.font.Font(None, 28)
                    cd_text = f"{cooldown:.1f}"
                    cd_surface = cd_font.render(cd_text, True, (255, 100, 100))
                    cd_rect = cd_surface.get_rect(center=(x + slot_size // 2, y + slot_size // 2))
                    screen.blit(cd_surface, cd_rect)
            else:
                # Empty slot
                pygame.draw.rect(screen, (40, 40, 50), slot_rect, border_radius=3)
                pygame.draw.rect(screen, (80, 80, 80), slot_rect, width=2, border_radius=3)
            
            # Key binding
            key_font = pygame.font.Font(None, 24)
            key_surface = key_font.render(keys[i], True, (255, 215, 0))
            key_rect = key_surface.get_rect(bottomright=(x + slot_size - 5, y + slot_size - 5))
            screen.blit(key_surface, key_rect)

    def _draw_projectiles(self, screen: pygame.Surface):
        """Draw all active projectiles."""
        for proj in self.projectiles:
            # Get projectile position in screen coordinates
            proj_x = int(proj["x"] - self.camera_x)
            proj_y = int(proj["y"] - self.camera_y)
            
            # Get direction for orientation
            dir_x = proj.get("direction_x", 1)
            dir_y = proj.get("direction_y", 0)
            width = int(proj.get("width", 20))
            
            # Draw projectile as circle with direction line
            pygame.draw.circle(screen, (255, 200, 0), (proj_x, proj_y), width // 2, 0)
            pygame.draw.circle(screen, (255, 255, 100), (proj_x, proj_y), width // 2, 2)
            
            # Draw direction indicator
            end_x = proj_x + dir_x * width
            end_y = proj_y + dir_y * width
            pygame.draw.line(screen, (255, 100, 0), (proj_x, proj_y), (int(end_x), int(end_y)), 3)

    def _cast_skill(self, skill_index: int):
        """Cast skill at given index."""
        # Validate skill index
        if skill_index >= len(self.equipped_skills):
            print(f"[Skill] No skill in slot {skill_index}")
            return
        
        skill = self.equipped_skills[skill_index]
        
        # Get local player
        if not self.local_player_id or self.local_player_id not in self.players:
            print(f"[Skill] Cannot cast - no local player")
            return
        
        local_player = self.players[self.local_player_id]
        
        # Check cooldown from server data
        if hasattr(local_player, 'skill_cooldowns') and len(local_player.skill_cooldowns) > skill_index:
            cooldown = local_player.skill_cooldowns[skill_index]
            if cooldown > 0:
                print(f"[Skill] {skill['name']} on cooldown ({cooldown:.1f}s)")
                return
        
        # Check mana (client-side prediction)
        mana_cost = skill.get("mana_cost", 0)
        if local_player.mana < mana_cost:
            print(f"[Skill] Not enough mana ({mana_cost} required, {int(local_player.mana)} available)")
            return
        
        # Send USE_SKILL packet to server
        packet = Packet(PacketType.USE_SKILL, {
            "skill_index": skill_index,
            "mouse_world_x": self.mouse_world_x,
            "mouse_world_y": self.mouse_world_y
        })
        self.manager.game.network.send(packet)
        
        print(f"[Skill] Cast {skill['name']} at ({int(self.mouse_world_x)}, {int(self.mouse_world_y)})")

    def on_exit(self):
            """Called when leaving game screen."""
            super().on_exit()
            # Show mouse cursor when leaving game
            pygame.mouse.set_visible(True)