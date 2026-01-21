# shared/packets.py
"""
Packet Definitions
Defines the structure of all network packets and provides serialization.
"""

import json
from typing import Any, Dict
from shared.enums import PacketType


class Packet:
    """Base packet class for network communication.""" 
    
    def __init__(self, packet_type: PacketType, data: Dict[str, Any] = None):
        self.type = packet_type
        self.data = data or {}
    
    def serialize(self) -> bytes:
        """Serialize packet to JSON bytes."""
        packet_dict = {
            "type": self.type.name,
            "data": self.data
        }
        return json.dumps(packet_dict).encode('utf-8')
    
    @staticmethod
    def deserialize(data: bytes) -> 'Packet':
        """Deserialize bytes to Packet object."""
        packet_dict = json.loads(data.decode('utf-8'))
        packet_type = PacketType[packet_dict["type"]]
        return Packet(packet_type, packet_dict.get("data", {}))
    
    def __repr__(self):
        return f"Packet(type={self.type.name}, data={self.data})"


class LoginRequest(Packet):
    """Login request from client to server."""
    
    def __init__(self, username: str, password: str):
        super().__init__(PacketType.LOGIN_REQUEST, {
            "username": username,
            "password": password
        })


class LoginResponse(Packet):
    """Login response from server to client."""
    
    def __init__(self, success: bool, message: str, user_id: int = None, stats: Dict = None):
        super().__init__(PacketType.LOGIN_RESPONSE, {
            "success": success,
            "message": message,
            "user_id": user_id,
            "stats": stats or {}
        })


class RegisterRequest(Packet):
    """Registration request from client to server."""
    
    def __init__(self, username: str, password: str, email: str = ""):
        super().__init__(PacketType.REGISTER_REQUEST, {
            "username": username,
            "password": password,
            "email": email
        })


class RegisterResponse(Packet):
    """Registration response from server to client."""
    
    def __init__(self, success: bool, message: str):
        super().__init__(PacketType.REGISTER_RESPONSE, {
            "success": success,
            "message": message
        })


class PlayerInput(Packet):
    """Player input from client to server."""
    
    def __init__(self, move_x: float, move_y: float, mouse_x: float = 0, 
                 mouse_y: float = 0, actions: Dict[str, bool] = None):
        super().__init__(PacketType.PLAYER_INPUT, {
            "move_x": move_x,
            "move_y": move_y,
            "mouse_x": mouse_x,
            "mouse_y": mouse_y,
            "actions": actions or {}
        })


class WorldState(Packet):
    """World state update from server to client."""
    
    def __init__(self, players: list, projectiles: list = None, zone_data: Dict = None):
        super().__init__(PacketType.WORLD_STATE, {
            "players": players,
            "projectiles": projectiles or [],
            "zone": zone_data or {}
        })


class LobbyState(Packet):
    """Lobby state update from server to client."""
    
    def __init__(self, players: list, match_starting: bool = False, countdown: int = 0):
        super().__init__(PacketType.LOBBY_STATE, {
            "players": players,
            "match_starting": match_starting,
            "countdown": countdown
        })


class ChatMessage(Packet):
    """Chat message packet."""
    
    def __init__(self, username: str, message: str, timestamp: float = None):
        import time
        super().__init__(PacketType.CHAT_MESSAGE, {
            "username": username,
            "message": message,
            "timestamp": timestamp or time.time()
        })
