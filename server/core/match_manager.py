# server/core/match_manager.py
"""
Match Manager
Manages active game matches and game loop.
"""

import asyncio
import time
from typing import Dict, Optional
from server.models.match import Match
from shared.constants import TICK_RATE
from shared.packets import WorldState, Packet
from shared.enums import PacketType


class MatchManager:
    """Manages active game matches."""
    
    def __init__(self, server):
        self.server = server
        self.matches: Dict[int, Match] = {}  # match_id -> Match
        self.active_match: Optional[Match] = None
        self.next_match_id = 1
        
        # Game loop
        self.is_running = False
        self.tick_rate = TICK_RATE
        self.tick_duration = 1.0 / self.tick_rate
    
    def create_match(self) -> Match:
        """Create a new match."""
        match_id = self.next_match_id
        self.next_match_id += 1
        
        match = Match(match_id)
        self.matches[match_id] = match
        
        print(f"[MatchManager] Created match {match_id}")
        return match
    
    def start_match(self, match_id: int):
        """Start a specific match."""
        match = self.matches.get(match_id)
        if not match:
            return
        
        match.start()
        self.active_match = match
        
        # Start game loop if not running
        if not self.is_running:
            asyncio.create_task(self._game_loop())
    
    def end_match(self, match_id: int):
        """End a specific match."""
        match = self.matches.get(match_id)
        if not match:
            return
        
        match.end()
        
        # Send match end packet
        match_end = Packet(PacketType.MATCH_END, {
            "match_id": match_id,
            "winner": self._get_winner(match),
            "stats": self._get_match_stats(match)
        })
        
        asyncio.create_task(self.server.socket.broadcast(match_end))
        
        # Clean up
        if self.active_match and self.active_match.match_id == match_id:
            self.active_match = None
    
    async def _game_loop(self):
        """Main server game loop."""
        self.is_running = True
        last_time = time.time()
        
        print("[MatchManager] Game loop started")
        
        while self.is_running:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time
            
            # Update active match
            if self.active_match:
                self.active_match.update(delta_time)
                
                # Broadcast world state to all clients
                await self._broadcast_world_state()
                
                # Check if match should end
                if self.active_match.state.name == "FINISHED":
                    self.end_match(self.active_match.match_id)
            else:
                # No active match, slow down loop
                await asyncio.sleep(0.1)
                continue
            
            # Sleep to maintain tick rate
            elapsed = time.time() - current_time
            sleep_time = max(0, self.tick_duration - elapsed)
            await asyncio.sleep(sleep_time)
        
        print("[MatchManager] Game loop stopped")
    
    async def _broadcast_world_state(self):
        """Send world state to all players in active match."""
        if not self.active_match:
            return
        
        # Serialize match state
        state_data = self.active_match.get_state_dict()
        
        # Create world state packet
        world_packet = WorldState(
            players=state_data["players"],
            projectiles=[],  # TODO: Add projectiles
            zone_data=state_data["zone"]
        )
        
        # Broadcast to all clients
        await self.server.socket.broadcast(world_packet)
    
    def _get_winner(self, match: Match) -> Optional[dict]:
        """Get match winner information."""
        alive_players = [p for p in match.players.values() if p.is_alive]
        
        if alive_players:
            winner = alive_players[0]
            return {
                "player_id": winner.player_id,
                "username": winner.username,
                "kills": winner.kills
            }
        
        # No winner if everyone died
        return None
    
    def _get_match_stats(self, match: Match) -> dict:
        """Get match statistics."""
        return {
            "duration": match.end_time - match.start_time if match.end_time else 0,
            "total_players": len(match.players),
            "total_kills": sum(p.kills for p in match.players.values())
        }
    
    def stop(self):
        """Stop the match manager."""
        self.is_running = False
        
        # End all active matches
        for match in list(self.matches.values()):
            match.end()