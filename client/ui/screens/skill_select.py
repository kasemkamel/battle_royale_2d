# client/ui/screens/skill_select.py
"""
Skill Selection Screen
Allows players to select 4 skills for their loadout before joining matches.
"""

import pygame
from client.ui.ui_manager import UIScreen, Button
from shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG_COLOR
from shared.enums import PacketType
from shared.packets import Packet


class SkillBox:
    """Represents one of the 4 equipped skill slots."""
    
    def __init__(self, x: int, y: int, width: int, height: int, slot_index: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.slot_index = slot_index
        self.skill = None  # Equipped skill data
        self.is_hovered = False
    
    def set_skill(self, skill_data: dict):
        """Equip a skill to this slot."""
        self.skill = skill_data
    
    def clear(self):
        """Remove skill from slot."""
        self.skill = None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return True
        return False
    
    def render(self, screen: pygame.Surface):
        """Render the skill box."""
        # Background
        bg_color = (80, 80, 100) if self.is_hovered else (60, 60, 80)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, width=3, border_radius=5)
        
        if self.skill:
            # Skill name
            font = pygame.font.Font(None, 28)
            name_surface = font.render(self.skill["name"], True, (255, 255, 255))
            name_rect = name_surface.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
            screen.blit(name_surface, name_rect)
            
            # Skill category
            cat_font = pygame.font.Font(None, 20)
            cat_text = self.skill["category"]
            cat_surface = cat_font.render(cat_text, True, (150, 200, 255))
            cat_rect = cat_surface.get_rect(center=(self.rect.centerx, self.rect.centery + 10))
            screen.blit(cat_surface, cat_rect)
            
            # Mana cost
            mana_text = f"Mana: {int(self.skill['mana_cost'])}"
            mana_surface = cat_font.render(mana_text, True, (100, 200, 255))
            mana_rect = mana_surface.get_rect(center=(self.rect.centerx, self.rect.centery + 30))
            screen.blit(mana_surface, mana_rect)
        else:
            # Empty slot
            font = pygame.font.Font(None, 32)
            text = f"Slot {self.slot_index + 1}"
            text_surface = font.render(text, True, (120, 120, 120))
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)


class SkillCard:
    """Represents a skill in the selection grid."""
    
    def __init__(self, x: int, y: int, width: int, height: int, skill_data: dict):
        self.rect = pygame.Rect(x, y, width, height)
        self.skill = skill_data
        self.is_hovered = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return True
        return False
    
    def render(self, screen: pygame.Surface):
        """Render the skill card."""
        # Background
        bg_color = (70, 110, 150) if self.is_hovered else (50, 90, 130)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=3)
        pygame.draw.rect(screen, (150, 150, 150), self.rect, width=2, border_radius=3)
        
        # Skill name
        font = pygame.font.Font(None, 22)
        name_surface = font.render(self.skill["name"], True, (255, 255, 255))
        name_rect = name_surface.get_rect(midtop=(self.rect.centerx, self.rect.y + 5))
        screen.blit(name_surface, name_rect)
        
        # Category badge
        cat_font = pygame.font.Font(None, 16)
        cat_surface = cat_font.render(self.skill["category"], True, (255, 215, 0))
        cat_rect = cat_surface.get_rect(midbottom=(self.rect.centerx, self.rect.bottom - 5))
        screen.blit(cat_surface, cat_rect)


class SkillSelectionScreen(UIScreen):
    """Skill selection interface."""
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Skill slots (top of screen)
        slot_width = 180
        slot_height = 100
        slot_spacing = 20
        slot_start_x = (SCREEN_WIDTH - (slot_width * 4 + slot_spacing * 3)) // 2
        slot_y = 50
        
        self.skill_boxes = []
        for i in range(4):
            x = slot_start_x + i * (slot_width + slot_spacing)
            self.skill_boxes.append(SkillBox(x, slot_y, slot_width, slot_height, i))
        
        # All available skills
        self.all_skills = []
        self.skill_cards = []
        
        # Selected skill for info panel
        self.selected_skill = None
        self.selected_slot = None  # Which box is selected for removal
        
        # Buttons
        self.back_button = Button(
            20, SCREEN_HEIGHT - 70, 120, 50, "Back", self.go_back
        )
        
        self.save_button = Button(
            SCREEN_WIDTH - 140, SCREEN_HEIGHT - 70, 120, 50, "Save", self.save_loadout
        )
        
        self.add_button = None  # Created dynamically
        self.remove_button = None  # Created dynamically
        
        # Scroll offset for skill list
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Status message
        self.status_message = ""
        self.status_color = (255, 255, 255)
    
    def on_enter(self):
        """Called when entering screen."""
        super().on_enter()
        self.status_message = "Loading skills..."
        
        # Request all skills from server
        packet = Packet(PacketType.GET_ALL_SKILLS)
        self.manager.game.network.send(packet)
    
    def receive_all_skills(self, skills_data: list):
        """Called when skills are received from server."""
        self.all_skills = skills_data
        self._create_skill_cards()
        
        # Load current loadout AFTER skills are loaded
        self._load_current_loadout()
        
        self.status_message = f"Loaded {len(skills_data)} skills"
        self.status_color = (0, 255, 0)
    
    def _create_skill_cards(self):
        """Create skill cards for all available skills."""
        self.skill_cards.clear()
        
        card_width = 150
        card_height = 70
        cards_per_row = 7
        card_spacing = 10
        start_x = 50
        start_y = 200
        
        for i, skill in enumerate(self.all_skills):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = start_x + col * (card_width + card_spacing)
            y = start_y + row * (card_height + card_spacing)
            
            self.skill_cards.append(SkillCard(x, y, card_width, card_height, skill))
        
        # Calculate max scroll
        total_rows = (len(self.all_skills) + cards_per_row - 1) // cards_per_row
        total_height = total_rows * (card_height + card_spacing)
        visible_height = SCREEN_HEIGHT - start_y - 100
        self.max_scroll = max(0, total_height - visible_height)
    
    def _load_current_loadout(self):
        """Load player's current skill loadout into boxes."""
        loadout = self.manager.game.game_state.user_data.get("skill_loadout", [])
        
        print(f"[SkillSelect] Loading loadout: {loadout}")
        print(f"[SkillSelect] Available skills: {len(self.all_skills)}")
        
        # Clear all boxes first
        for box in self.skill_boxes:
            box.clear()
        
        # Load skills into boxes
        for i, skill_id in enumerate(loadout):
            if i >= 4:
                break
            
            # Find skill data
            skill_data = next((s for s in self.all_skills if s["skill_id"] == skill_id), None)
            if skill_data:
                self.skill_boxes[i].set_skill(skill_data)
                print(f"[SkillSelect] Loaded {skill_data['name']} into slot {i}")
            else:
                print(f"[SkillSelect] Warning: Skill '{skill_id}' not found in database")
    
    def go_back(self):
        """Navigate back to lobby."""
        self.manager.switch_to("lobby")
    
    def save_loadout(self):
        """Save current loadout to server."""
        # Get skill IDs from boxes
        skill_ids = []
        for box in self.skill_boxes:
            if box.skill:
                skill_ids.append(box.skill["skill_id"])
        
        # Send to server
        packet = Packet(PacketType.UPDATE_SKILL_LOADOUT, {
            "skill_loadout": skill_ids
        })
        self.manager.game.network.send(packet)
        
        self.status_message = "Saving..."
        self.status_color = (255, 255, 100)
    
    def on_save_response(self, success: bool, message: str, loadout: list):
        """Called when save response received."""
        if success:
            self.status_message = "Loadout saved!"
            self.status_color = (0, 255, 0)
            # Loadout is already updated in game state by game.py
            print(f"[SkillSelect] Loadout saved successfully: {loadout}")
        else:
            self.status_message = f"Error: {message}"
            self.status_color = (255, 100, 100)
            print(f"[SkillSelect] Save failed: {message}")
    
    def handle_event(self, event: pygame.event.Event):
        """Handle events."""
        # Handle scroll
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 30
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        # Handle buttons
        self.back_button.handle_event(event)
        self.save_button.handle_event(event)
        
        if self.add_button:
            if self.add_button.handle_event(event):
                self._add_selected_skill()
        
        if self.remove_button:
            if self.remove_button.handle_event(event):
                self._remove_selected_skill()
        
        # Handle skill boxes
        for box in self.skill_boxes:
            if box.handle_event(event):
                if box.skill:
                    # Select for removal
                    self.selected_skill = box.skill
                    self.selected_slot = box
                    self._create_remove_button()
                else:
                    # Empty slot clicked
                    self.selected_slot = None
        
        # Handle skill cards (with scroll offset)
        for card in self.skill_cards:
            # Adjust card position for scroll
            original_y = card.rect.y
            card.rect.y -= self.scroll_offset
            
            if card.handle_event(event):
                self.selected_skill = card.skill
                self.selected_slot = None
                self._create_add_button()
            
            # Restore position
            card.rect.y = original_y
    
    def _create_add_button(self):
        """Create the Add button in info panel."""
        self.add_button = Button(
            SCREEN_WIDTH - 320, SCREEN_HEIGHT - 180, 100, 40, "Add", None
        )
        self.remove_button = None
    
    def _create_remove_button(self):
        """Create the Remove button in info panel."""
        self.remove_button = Button(
            SCREEN_WIDTH - 320, SCREEN_HEIGHT - 180, 100, 40, "Remove", None
        )
        self.add_button = None
    
    def _add_selected_skill(self):
        """Add selected skill to first empty slot."""
        if not self.selected_skill:
            return
        
        # Check if already equipped
        for box in self.skill_boxes:
            if box.skill and box.skill["skill_id"] == self.selected_skill["skill_id"]:
                self.status_message = "Skill already equipped!"
                self.status_color = (255, 100, 100)
                return
        
        # Find first empty slot
        for box in self.skill_boxes:
            if not box.skill:
                box.set_skill(self.selected_skill)
                self.status_message = f"Added {self.selected_skill['name']}"
                self.status_color = (0, 255, 0)
                return
        
        self.status_message = "All slots full!"
        self.status_color = (255, 100, 100)
    
    def _remove_selected_skill(self):
        """Remove skill from selected slot."""
        if self.selected_slot and self.selected_slot.skill:
            skill_name = self.selected_slot.skill["name"]
            self.selected_slot.clear()
            self.status_message = f"Removed {skill_name}"
            self.status_color = (255, 200, 0)
            self.selected_skill = None
            self.selected_slot = None
            self.remove_button = None
    
    def render(self, screen: pygame.Surface):
        """Render the skill selection screen."""
        screen.fill(UI_BG_COLOR)
        
        # Title
        title_font = pygame.font.Font(None, 56)
        title_surface = title_font.render("SKILL SELECTION", True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 20))
        screen.blit(title_surface, title_rect)
        
        # Skill boxes (equipped skills)
        for box in self.skill_boxes:
            box.render(screen)
        
        # Divider line
        pygame.draw.line(screen, (100, 100, 100), (50, 170), (SCREEN_WIDTH - 50, 170), 2)
        
        # Label for available skills
        label_font = pygame.font.Font(None, 32)
        label_surface = label_font.render("Available Skills", True, (200, 200, 200))
        screen.blit(label_surface, (50, 175))
        
        # Create clip region for scrollable area
        clip_rect = pygame.Rect(0, 200, SCREEN_WIDTH, SCREEN_HEIGHT - 300)
        screen.set_clip(clip_rect)
        
        # Skill cards (scrollable)
        for card in self.skill_cards:
            # Adjust position for scroll
            original_y = card.rect.y
            card.rect.y -= self.scroll_offset
            
            # Only render if visible
            if card.rect.bottom > 200 and card.rect.top < SCREEN_HEIGHT - 100:
                card.render(screen)
            
            # Restore position
            card.rect.y = original_y
        
        # Remove clip
        screen.set_clip(None)
        
        # Info panel (bottom right)
        self._draw_info_panel(screen)
        
        # Buttons
        self.back_button.render(screen)
        self.save_button.render(screen)
        
        if self.add_button:
            self.add_button.render(screen)
        if self.remove_button:
            self.remove_button.render(screen)
        
        # Status message
        if self.status_message:
            status_font = pygame.font.Font(None, 24)
            status_surface = status_font.render(self.status_message, True, self.status_color)
            status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35))
            screen.blit(status_surface, status_rect)
    
    def _draw_info_panel(self, screen: pygame.Surface):
        """Draw skill info panel."""
        panel_rect = pygame.Rect(SCREEN_WIDTH - 350, SCREEN_HEIGHT - 240, 330, 150)
        pygame.draw.rect(screen, (40, 40, 50), panel_rect, border_radius=5)
        pygame.draw.rect(screen, (150, 150, 150), panel_rect, width=2, border_radius=5)
        
        if self.selected_skill:
            font = pygame.font.Font(None, 26)
            small_font = pygame.font.Font(None, 20)
            
            y_offset = panel_rect.y + 10
            
            # Skill name
            name_surface = font.render(self.selected_skill["name"], True, (255, 215, 0))
            screen.blit(name_surface, (panel_rect.x + 10, y_offset))
            y_offset += 30
            
            # Category
            cat_text = f"Type: {self.selected_skill['category']}"
            cat_surface = small_font.render(cat_text, True, (150, 200, 255))
            screen.blit(cat_surface, (panel_rect.x + 10, y_offset))
            y_offset += 25
            
            # Stats
            stats = [
                f"Damage: {int(self.selected_skill.get('damage', 0))}",
                f"Mana: {int(self.selected_skill['mana_cost'])}",
                f"Cooldown: {self.selected_skill['cooldown']:.1f}s",
                f"Range: {int(self.selected_skill.get('cast_range', 0))}"
            ]
            
            for stat in stats:
                stat_surface = small_font.render(stat, True, (200, 200, 200))
                screen.blit(stat_surface, (panel_rect.x + 10, y_offset))
                y_offset += 20
        else:
            # Prompt
            font = pygame.font.Font(None, 22)
            text = "Click a skill for details"
            text_surface = font.render(text, True, (120, 120, 120))
            text_rect = text_surface.get_rect(center=panel_rect.center)
            screen.blit(text_surface, text_rect)