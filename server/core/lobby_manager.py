# server/core/lobby_manager.py
"""
Lobby Manager
Manages pre-game lobby, player readiness, and match starting.
"""

import time
from typing import Dict, Optional
from server.models.player import Player
from shared.constants import MIN_PLAYERS, LOBBY_WAIT_TIME


class LobbyManager:
    """Manages the game lobby before matches start."""
    
    def __init__(self, server):
        self.server = server
        self.players: Dict[int, Player] = {}  # player_id -> Player
        self.next_player_id = 1
        
        # Match starting
        self.match_starting = False
        self.countdown_start = None
        self.countdown_duration = LOBBY_WAIT_TIME
    
    def add_player(self, user_id: int, conn_id: int) -> Optional[Player]:
        """Add a player to the lobby."""
        # Get user info from authenticator
        user = self.server.authenticator.get_session(user_id)
        if not user:
            return None
        
        # Check if player already exists in lobby (prevent duplicates)
        for existing_player in self.players.values():
            if existing_player.user_id == user_id:
                print(f"[Lobby] Player {user.username} already in lobby, skipping duplicate")
                return existing_player
        
        # Create player
        player_id = self.next_player_id
        self.next_player_id += 1
        
        player = Player(player_id, user_id, user.username)
        self.players[player_id] = player
        
        print(f"[Lobby] {user.username} joined lobby ({len(self.players)} players)")
        
        # Check if we can start match
        self._check_start_match()
        
        return player
    
    def remove_player(self, player_id: int):
        """Remove a player from the lobby."""
        if player_id in self.players:
            player = self.players[player_id]
            del self.players[player_id]
            print(f"[Lobby] {player.username} left lobby ({len(self.players)} players)")
            
            # Cancel countdown if not enough players
            if len(self.players) < MIN_PLAYERS:
                self.match_starting = False
                self.countdown_start = None
    
    def set_player_ready(self, player_id: int, ready: bool):
        """Set player ready status."""
        if player_id in self.players:
            self.players[player_id].ready = ready
            print(f"[Lobby] {self.players[player_id].username} ready: {ready}")
            
            self._check_start_match()
    
    def _check_start_match(self):
        """Check if match can start."""
        # Need minimum players
        if len(self.players) < MIN_PLAYERS:
            return
        
        # Check if all players are ready
        all_ready = all(p.ready for p in self.players.values())
        
        if all_ready and not self.match_starting:
            # Start countdown
            self.match_starting = True
            self.countdown_start = time.time()
            print(f"[Lobby] Match starting in {self.countdown_duration} seconds...")
    
    def update(self) -> bool:
        """
        Update lobby state (check countdown).
        Returns True if lobby state changed and should be broadcast.
        """
        if not self.match_starting:
            return False
        
        # Check if countdown finished
        if time.time() - self.countdown_start >= self.countdown_duration:
            self._start_match()
            return False  # Match started, lobby cleared
        
        # Countdown is active, state should be broadcast
        return True
    
    def _start_match(self):
        """Start the match with current lobby players."""
        print(f"[Lobby] Starting match with {len(self.players)} players")
        
        match = self.server.match_manager.create_match()
        
        for player in list(self.players.values()):
            user = self.server.authenticator.get_session(player.user_id)
            if user:
                # 1. Load skills
                player.skills = []
                for skill_id in user.skill_loadout:
                    base_skill = self.server.skill_database.get_skill(skill_id)
                    if base_skill:
                        import copy
                        skill_instance = copy.deepcopy(base_skill)
                        player.skills.append(skill_instance)
                
                print(f"[Lobby] Loaded {len(player.skills)} skills for {player.username}")
                
                # 2. Apply passive bonuses AFTER skills are loaded
                player.apply_passive_bonuses()
            
            match.add_player(player)
            
            # Clear lobby (players are now in match, will return after match ends)
            self.players.clear()
            self.match_starting = False
            self.countdown_start = None
            
        # Start the match
        self.server.match_manager.start_match(match.match_id)
    
    def get_lobby_state(self) -> dict:
        """Get current lobby state."""
        countdown = 0
        if self.match_starting and self.countdown_start:
            elapsed = time.time() - self.countdown_start
            countdown = max(0, int(self.countdown_duration - elapsed))
        
        return {
            "players": [
                {
                    "player_id": p.player_id,
                    "user_id": p.user_id,  # Include user_id for client matching
                    "username": p.username,
                    "ready": p.ready
                }
                for p in self.players.values()
            ],
            "match_starting": self.match_starting,
            "countdown": countdown
        }