# client/network/client.py
"""
Network Client
Handles connection to server and async packet communication.
"""

import asyncio
import threading
from typing import Callable, Optional
from shared.constants import SERVER_HOST, SERVER_PORT
from shared.packets import Packet
from shared.enums import PacketType


class NetworkClient:
    """Async network client for connecting to game server."""
    
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_connected = False
        
        # Callbacks
        self.packet_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        
        # Threading
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
    
    def set_packet_callback(self, callback: Callable):
        """Set callback for received packets: callback(packet)"""
        self.packet_callback = callback
    
    def set_connection_callback(self, callback: Callable):
        """Set callback for connection state changes: callback(connected: bool)"""
        self.connection_callback = callback
    
    def connect(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        """Connect to server (non-blocking)."""
        if self.is_connected:
            print("[Client] Already connected")
            return
        
        # Start network thread
        self.thread = threading.Thread(target=self._run_async_loop, args=(host, port), daemon=True)
        self.thread.start()
    
    def _run_async_loop(self, host: str, port: int):
        """Run async event loop in separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._connect_and_listen(host, port))
        except Exception as e:
            print(f"[Client] Network error: {e}")
        finally:
            self.loop.close()
    
    async def _connect_and_listen(self, host: str, port: int):
        """Connect to server and listen for packets."""
        try:
            # Connect
            self.reader, self.writer = await asyncio.open_connection(host, port)
            self.is_connected = True
            
            print(f"[Client] Connected to {host}:{port}")
            
            # Notify connection callback
            if self.connection_callback:
                self.connection_callback(True)
            
            # Listen for packets
            while self.is_connected:
                packet = await self._receive_packet()
                
                if packet is None:
                    break
                
                # Handle packet through callback
                if self.packet_callback:
                    self.packet_callback(packet)
        
        except ConnectionRefusedError:
            print("[Client] Connection refused - is the server running?")
        except Exception as e:
            print(f"[Client] Connection error: {e}")
        finally:
            self.disconnect()
    
    async def _receive_packet(self) -> Optional[Packet]:
        """Receive a packet from server."""
        try:
            # Read length header (4 bytes)
            length_bytes = await self.reader.readexactly(4)
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read packet data
            data = await self.reader.readexactly(length)
            return Packet.deserialize(data)
        
        except asyncio.IncompleteReadError:
            return None
        except Exception as e:
            print(f"[Client] Receive error: {e}")
            return None
    
    def send(self, packet: Packet):
        """Send packet to server (non-blocking)."""
        if not self.is_connected or not self.loop:
            return
        
        # Schedule send in async loop
        asyncio.run_coroutine_threadsafe(self._send_packet(packet), self.loop)
    
    async def _send_packet(self, packet: Packet):
        """Async send packet."""
        if not self.is_connected or not self.writer:
            return
        
        try:
            data = packet.serialize()
            length = len(data).to_bytes(4, byteorder='big')
            
            self.writer.write(length + data)
            await self.writer.drain()
        
        except Exception as e:
            print(f"[Client] Send error: {e}")
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from server."""
        if not self.is_connected:
            return
        
        self.is_connected = False
        
        if self.writer:
            self.writer.close()
        
        # Notify connection callback
        if self.connection_callback:
            self.connection_callback(False)
        
        print("[Client] Disconnected from server")
    
    # Convenience methods for common packets
    
    def send_login(self, username: str, password: str):
        """Send login request."""
        from shared.packets import LoginRequest
        self.send(LoginRequest(username, password))
    
    def send_register(self, username: str, password: str, email: str = ""):
        """Send registration request."""
        from shared.packets import RegisterRequest
        self.send(RegisterRequest(username, password, email))
    
    def send_player_input(self, move_x: float, move_y: float, mouse_x: float = 0, 
                          mouse_y: float = 0, actions: dict = None):
        """Send player input."""
        from shared.packets import PlayerInput
        self.send(PlayerInput(move_x, move_y, mouse_x, mouse_y, actions))
    
    def send_join_lobby(self):
        """Send join lobby request."""
        self.send(Packet(PacketType.JOIN_LOBBY))
    
    def send_player_ready(self, ready: bool = True):
        """Send player ready status."""
        self.send(Packet(PacketType.PLAYER_READY, {"ready": ready}))