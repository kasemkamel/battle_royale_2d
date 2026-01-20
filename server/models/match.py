# server/models/match.py
"""
Match Model
Represents a game match instance with players and game state.
"""

import time
import random
from typing import Dict, List
from shared.enums import MatchState, PlayerState
from shared.constants import (
    WORLD_WIDTH, WORLD_HEIGHT, MATCH_DURATION,
    ZONE_INITIAL_RADIUS, ZONE_SHRINK_RATE
)
from server.models.player import Player


class Match:
    """Game match instance managing players and match state."""
    
    def __init__(self, match_id: int):
        self.match_id = match_id
        self.state = MatchState.WAITING
        self.players: Dict[int, Player] = {}  # player_id -> Player
        
        # Timing
        self.start_time = None
        self.end_time = None
        self.duration = MATCH_DURATION
        
        # Zone (Battle Royale shrinking area)
        self.zone_center_x = WORLD_WIDTH / 2
        self.zone_center_y = WORLD_HEIGHT / 2
        self.zone_radius = ZONE_INITIAL_RADIUS
        self.zone_target_radius = ZONE_INITIAL_RADIUS
        
        # Stats
        self.tick_count = 0
    
    def add_player(self, player: Player):
        """Add a player to the match."""
        self.players[player.player_id] = player
        player.state = PlayerState.LOBBY
        print(f"[Match {self.match_id}] Player {player.username} joined ({len(self.players)} total)")
    
    def remove_player(self, player_id: int):
        """Remove a player from the match."""
        if player_id in self.players:
            player = self.players[player_id]
            del self.players[player_id]
            print(f"[Match {self.match_id}] Player {player.username} left ({len(self.players)} remaining)")
    
    def start(self):
        """Start the match."""
        if self.state != MatchState.WAITING:
            return
        
        self.state = MatchState.ACTIVE
        self.start_time = time.time()
        
        # Spawn all players at random positions
        for player in self.players.values():
            spawn_x = random.uniform(100, WORLD_WIDTH - 100)
            spawn_y = random.uniform(100, WORLD_HEIGHT - 100)
            player.respawn(spawn_x, spawn_y)
            player.state = PlayerState.IN_GAME
        
        print(f"[Match {self.match_id}] Started with {len(self.players)} players")
    
    def update(self, delta_time: float):
        """Update match state (called every server tick)."""
        if self.state != MatchState.ACTIVE:
            return
        
        self.tick_count += 1
        
        # Update all players
        for player in self.players.values():
            player.update(delta_time)
        
        # Update zone (shrink over time)
        if self.zone_radius > 100:  # Minimum zone size
            self.zone_radius -= ZONE_SHRINK_RATE * delta_time
        
        # Apply zone damage to players outside
        self._apply_zone_damage()
        
        # Check win condition
        self._check_win_condition()
        
        # Check time limit
        if time.time() - self.start_time > self.duration:
            self.end()
    
    def _apply_zone_damage(self):
        """Apply damage to players outside the safe zone."""
        for player in self.players.values():
            if not player.is_alive:
                continue
            
            # Calculate distance from zone center
            dx = player.x - self.zone_center_x
            dy = player.y - self.zone_center_y
            distance = (dx**2 + dy**2)**0.5
            
            # Apply damage if outside zone
            if distance > self.zone_radius:
                player.take_damage(5)  # 5 damage per tick when outside
    
    def _check_win_condition(self):
        """Check if match should end (only one player alive)."""
        alive_players = [p for p in self.players.values() if p.is_alive]
        
        if len(alive_players) <= 1:
            self.end()
    
    def end(self):
        """End the match."""
        if self.state == MatchState.FINISHED:
            return
        
        self.state = MatchState.FINISHED
        self.end_time = time.time()
        
        # Determine winner
        winner = None
        alive_players = [p for p in self.players.values() if p.is_alive]
        if alive_players:
            winner = alive_players[0]
        
        if winner:
            print(f"[Match {self.match_id}] Winner: {winner.username}")
        else:
            print(f"[Match {self.match_id}] No winner (time limit reached)")
    
    def get_state_dict(self) -> dict:
        """Get match state as dictionary for network transmission."""
        return {
            "match_id": self.match_id,
            "state": self.state.name,
            "players": [p.to_dict() for p in self.players.values()],
            "zone": {
                "center_x": self.zone_center_x,
                "center_y": self.zone_center_y,
                "radius": self.zone_radius
            },
            "time_remaining": self.get_time_remaining()
        }
    
    def get_time_remaining(self) -> float:
        """Get remaining match time in seconds."""
        if self.state != MatchState.ACTIVE or not self.start_time:
            return self.duration
        
        elapsed = time.time() - self.start_time
        return max(0, self.duration - elapsed)
    
    def __repr__(self):
        return f"Match(id={self.match_id}, state={self.state.name}, players={len(self.players)})"