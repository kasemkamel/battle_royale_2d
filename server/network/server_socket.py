# server/network/server_socket.py
"""
Server Socket
Async TCP server for handling multiple client connections.
"""

import asyncio
import traceback
from typing import Dict, Callable
from shared.constants import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from shared.packets import Packet


class ClientConnection:
    """Represents a single client connection."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, conn_id: int):
        self.reader = reader
        self.writer = writer
        self.conn_id = conn_id
        self.user_id = None
        self.player_id = None
        self.address = writer.get_extra_info('peername')
        self.is_connected = True
    
    async def send(self, packet: Packet):
        """Send a packet to this client."""
        if not self.is_connected:
            return
        
        try:
            data = packet.serialize()
            # Prepend length header (4 bytes)
            length = len(data).to_bytes(4, byteorder='big')
            self.writer.write(length + data)
            await self.writer.drain()
        except Exception as e:
            print(f"[Server] Error sending to client {self.conn_id}: {e}")
            self.is_connected = False
    
    async def receive(self) -> Packet:
        """Receive a packet from this client."""
        try:
            # Read length header (4 bytes)
            length_bytes = await self.reader.readexactly(4)
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read packet data
            data = await self.reader.readexactly(length)
            return Packet.deserialize(data)
        except asyncio.IncompleteReadError:
            self.is_connected = False
            return None
        except Exception as e:
            print(f"[Server] Error receiving from client {self.conn_id}: {e}")
            self.is_connected = False
            return None
    
    def close(self):
        """Close the connection."""
        self.is_connected = False
        self.writer.close()


class ServerSocket:
    """Async TCP server managing multiple client connections."""
    
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.clients: Dict[int, ClientConnection] = {}  # conn_id -> ClientConnection
        self.next_conn_id = 1
        self.is_running = False
        
        # Callback for packet handling
        self.packet_handler: Callable = None
    
    def set_packet_handler(self, handler: Callable):
        """Set the callback function for handling incoming packets."""
        self.packet_handler = handler
    
    async def start(self):
        """Start the server."""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        
        self.is_running = True
        addr = self.server.sockets[0].getsockname()
        print(f"[Server] Listening on {addr[0]}:{addr[1]}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        conn_id = self.next_conn_id
        self.next_conn_id += 1
        
        client = ClientConnection(reader, writer, conn_id)
        self.clients[conn_id] = client
        
        print(f"[Server] Client {conn_id} connected from {client.address}")
        
        try:
            # Receive packets from client
            while client.is_connected:
                packet = await client.receive()
                
                if packet is None:
                    break
                
                # Handle packet through callback
                if self.packet_handler:
                    await self.packet_handler(client, packet)
        
        except Exception as e:
            print(f"[Server] Error handling client {conn_id}: {e}")
            traceback.print_exc()
        
        finally:
            # Clean up
            print(f"[Server] Client {conn_id} disconnected")
            client.close()
            if conn_id in self.clients:
                del self.clients[conn_id]
    
    async def broadcast(self, packet: Packet, exclude_conn_id: int = None):
        """Send packet to all connected clients."""
        tasks = []
        for conn_id, client in list(self.clients.items()):
            if exclude_conn_id and conn_id == exclude_conn_id:
                continue
            tasks.append(client.send(packet))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_client(self, conn_id: int, packet: Packet):
        """Send packet to a specific client."""
        client = self.clients.get(conn_id)
        if client:
            await client.send(packet)
    
    def get_client(self, conn_id: int) -> ClientConnection:
        """Get client by connection ID."""
        return self.clients.get(conn_id)
    
    def stop(self):
        """Stop the server."""
        self.is_running = False
        if self.server:
            self.server.close()
        
        # Close all client connections
        for client in self.clients.values():
            client.close()
        
        print("[Server] Server stopped")