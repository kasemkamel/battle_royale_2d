# server\network\packet_handler.py
"""
Server Packet Handler
Routes incoming packets to appropriate handler methods.
"""

from shared.enums import PacketType
from shared.packets import Packet, LoginResponse, RegisterResponse, LobbyState
from server.network.server_socket import ClientConnection


class ServerPacketHandler:
    """Handles incoming packets from clients."""
    
    def __init__(self, server):
        """
        server: The main GameServer instance with auth, lobby, etc.
        """
        self.server = server
    
    async def handle_packet(self, client: ClientConnection, packet: Packet):
        """Route packet to appropriate handler."""
        handlers = {
            PacketType.LOGIN_REQUEST: self._handle_login,
            PacketType.REGISTER_REQUEST: self._handle_register,
            PacketType.LOGOUT: self._handle_logout,
            PacketType.JOIN_LOBBY: self._handle_join_lobby,
            PacketType.LEAVE_LOBBY: self._handle_leave_lobby,
            PacketType.PLAYER_READY: self._handle_player_ready,
            PacketType.PLAYER_INPUT: self._handle_player_input,
            PacketType.CHAT_MESSAGE: self._handle_chat,
            PacketType.PING: self._handle_ping,
        }
        
        handler = handlers.get(packet.type)
        if handler:
            await handler(client, packet)
        else:
            print(f"[Server] Unhandled packet type: {packet.type}")
    
    async def _handle_login(self, client: ClientConnection, packet: Packet):
        """Handle login request."""
        username = packet.data.get("username")
        password = packet.data.get("password")
        
        success, message, user = self.server.authenticator.login(username, password)
        
        if success:
            client.user_id = user.user_id
            response = LoginResponse(
                success=True,
                message=message,
                user_id=user.user_id,
                stats=user.stats
            )
        else:
            response = LoginResponse(success=False, message=message)
        
        await client.send(response)
    
    async def _handle_register(self, client: ClientConnection, packet: Packet):
        """Handle registration request."""
        username = packet.data.get("username")
        password = packet.data.get("password")
        email = packet.data.get("email", "")
        
        success, message, user = self.server.authenticator.register(username, password, email)
        
        response = RegisterResponse(success=success, message=message)
        await client.send(response)
    
    async def _handle_logout(self, client: ClientConnection, packet: Packet):
        """Handle logout."""
        if client.user_id:
            self.server.authenticator.logout(client.user_id)
            client.user_id = None
    
    async def _handle_join_lobby(self, client: ClientConnection, packet: Packet):
        """Handle join lobby request."""
        if not client.user_id:
            return
        
        # If client already has a player_id, don't add again
        if client.player_id:
            print(f"[Server] Client {client.conn_id} already has player_id {client.player_id}")
            await self._broadcast_lobby_state()
            return
        
        # Add player to lobby
        player = self.server.lobby_manager.add_player(client.user_id, client.conn_id)
        if player:
            client.player_id = player.player_id
            
            # Send lobby state to all players
            await self._broadcast_lobby_state()
    
    async def _handle_leave_lobby(self, client: ClientConnection, packet: Packet):
        """Handle leave lobby request."""
        if client.player_id:
            self.server.lobby_manager.remove_player(client.player_id)
            client.player_id = None
            
            await self._broadcast_lobby_state()
    
    async def _handle_player_ready(self, client: ClientConnection, packet: Packet):
        """Handle player ready toggle."""
        if not client.player_id:
            return
        
        ready = packet.data.get("ready", True)
        self.server.lobby_manager.set_player_ready(client.player_id, ready)
        
        await self._broadcast_lobby_state()
    
    async def _handle_player_input(self, client: ClientConnection, packet: Packet):
        """Handle player input during gameplay."""
        if not client.player_id:
            return
        
        # Forward to match manager
        move_x = packet.data.get("move_x", 0)
        move_y = packet.data.get("move_y", 0)
        actions = packet.data.get("actions", {})
        
        # Update player input in active match
        if self.server.match_manager.active_match:
            match = self.server.match_manager.active_match
            player = match.players.get(client.player_id)
            if player:
                player.set_input(move_x, move_y, actions)
    
    async def _handle_chat(self, client: ClientConnection, packet: Packet):
        """Handle chat message."""
        # Broadcast chat to all clients
        await self.server.socket.broadcast(packet)
    
    async def _handle_ping(self, client: ClientConnection, packet: Packet):
        """Handle ping request."""
        pong = Packet(PacketType.PONG, {"timestamp": packet.data.get("timestamp")})
        await client.send(pong)
    
    async def _broadcast_lobby_state(self):
        """Send lobby state to all lobby players."""
        lobby_data = self.server.lobby_manager.get_lobby_state()
        lobby_packet = LobbyState(
            players=lobby_data["players"],
            match_starting=lobby_data["match_starting"],
            countdown=lobby_data["countdown"]
        )
        await self.server.socket.broadcast(lobby_packet)