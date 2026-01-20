# server/core/server.py
"""
Game Server
Main server orchestrator that coordinates all server subsystems.
"""

import asyncio
from server.network.server_socket import ServerSocket
from server.network.packet_handler import ServerPacketHandler
from server.auth.database import Database
from server.auth.authenticator import Authenticator
from server.core.lobby_manager import LobbyManager
from server.core.match_manager import MatchManager


class GameServer:
    """Main game server managing all subsystems."""
    
    def __init__(self):
        # Initialize subsystems
        self.socket = ServerSocket()
        self.database = Database()
        self.authenticator = Authenticator(self.database)
        self.lobby_manager = LobbyManager(self)
        self.match_manager = MatchManager(self)
        
        # Set up packet handler
        self.packet_handler = ServerPacketHandler(self)
        self.socket.set_packet_handler(self.packet_handler.handle_packet)
        
        # State
        self.is_running = False
        
        print("[Server] Game server initialized")
    
    async def start(self):
        """Start the game server."""
        print("[Server] Starting game server...")
        self.is_running = True
        
        # Start lobby update loop
        asyncio.create_task(self._lobby_update_loop())
        
        # Start network server (this blocks)
        await self.socket.start()
    
    async def _lobby_update_loop(self):
        """Update lobby state periodically."""
        while self.is_running:
            self.lobby_manager.update()
            await asyncio.sleep(1.0)  # Update every second
    
    def stop(self):
        """Stop the game server."""
        print("[Server] Stopping game server...")
        self.is_running = False
        
        # Stop subsystems
        self.match_manager.stop()
        self.socket.stop()
        self.database.close()
        
        print("[Server] Server stopped")
    
    async def shutdown(self):
        """Graceful shutdown."""
        self.stop()
        await asyncio.sleep(1)  # Give time for cleanup