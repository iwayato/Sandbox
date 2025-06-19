import asyncio
import websockets
import json
import socket
from datetime import datetime

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        
    def get_local_ip(self):
        """Get the local IP address of this machine"""
        try:
            # Connect to a remote server to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    async def register_client(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister a client"""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_message(self, message, sender=None):
        """Broadcast message to all connected clients except sender"""
        if self.clients:
            # Send to all clients except the sender
            recipients = self.clients - {sender} if sender else self.clients
            if recipients:
                await asyncio.gather(
                    *[client.send(message) for client in recipients],
                    return_exceptions=True
                )
    
    async def handle_client(self, websocket):
        """Handle individual client connections"""
        await self.register_client(websocket)
        
        try:
            # Send welcome message
            welcome_msg = {
                "type": "welcome",
                "message": "Connected to WebSocket server",
                "timestamp": datetime.now().isoformat(),
                "server_ip": self.get_local_ip()
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Listen for messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"Received: {data}")
                    
                    # Echo the message back with server info
                    response = {
                        "type": "echo",
                        "original_message": data,
                        "server_response": f"Server received: {data.get('message', 'No message')}",
                        "timestamp": datetime.now().isoformat(),
                        "clients_connected": len(self.clients)
                    }
                    
                    # Send response back to sender
                    await websocket.send(json.dumps(response))
                    
                    # Broadcast to other clients
                    broadcast_msg = {
                        "type": "broadcast",
                        "from_client": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.broadcast_message(json.dumps(broadcast_msg), sender=websocket)
                    
                except json.JSONDecodeError:
                    error_msg = {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(error_msg))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        local_ip = self.get_local_ip()
        print(f"Starting WebSocket server on {local_ip}:{self.port}")
        print(f"Server accessible at: ws://{local_ip}:{self.port}")
        print("Waiting for connections...")
        
        server = await websockets.serve(self.handle_client, self.host, self.port)
        await server.wait_closed()

if __name__ == "__main__":
    server = WebSocketServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nServer stopped by user")