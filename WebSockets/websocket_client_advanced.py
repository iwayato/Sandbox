import asyncio
import websockets
import json
import threading
import sys
import time
from datetime import datetime

class AdvancedWebSocketClient:
    def __init__(self, server_ip, server_port=8765):
        self.server_ip = server_ip
        self.server_port = server_port
        self.websocket = None
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 10
        
    async def connect_to_server(self):
        """Connect to the WebSocket server with retry logic"""
        uri = f"ws://{self.server_ip}:{self.server_port}"
        
        for attempt in range(self.max_reconnect_attempts):
            try:
                print(f"Connection attempt {attempt + 1}/{self.max_reconnect_attempts}")
                self.websocket = await websockets.connect(uri, ping_interval=20, ping_timeout=10)
                self.running = True
                print("Connected successfully!")
                return True
            except Exception as e:
                print(f"Connection failed: {e}")
                if attempt < self.max_reconnect_attempts - 1:
                    print(f"Retrying in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    print("Max reconnection attempts reached")
                    return False
        
        return False
    
    async def send_message(self, message):
        """Send message to server with error handling"""
        if not self.websocket or self.websocket.closed:
            print("Not connected to server")
            return False
            
        try:
            msg_data = {
                "message": message,
                "client_timestamp": datetime.now().isoformat(),
                "type": "client_message"
            }
            await self.websocket.send(json.dumps(msg_data))
            print(f"✓ Sent: {message}")
            return True
        except Exception as e:
            print(f"✗ Error sending message: {e}")
            return False
    
    async def listen_for_messages(self):
        """Listen for messages with auto-reconnection"""
        while self.running:
            try:
                if not self.websocket or self.websocket.closed:
                    print("Connection lost, attempting to reconnect...")
                    if not await self.connect_to_server():
                        break
                
                async for message in self.websocket:
                    try:
                        data = json.loads(message)
                        self.handle_server_message(data)
                    except json.JSONDecodeError:
                        print(f"Received non-JSON: {message}")
                        
            except websockets.exceptions.ConnectionClosed:
                print("Server connection closed")
                if self.running:
                    print("Attempting to reconnect...")
                    await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                print(f"Error in message listener: {e}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
    
    def handle_server_message(self, data):
        """Handle different types of server messages"""
        msg_type = data.get('type', 'unknown')
        
        if msg_type == 'welcome':
            print(f"🎉 {data.get('message')}")
            print(f"   Server IP: {data.get('server_ip')}")
        elif msg_type == 'echo':
            print(f"🔄 Server echo: {data.get('server_response')}")
        elif msg_type == 'broadcast':
            print(f"📢 Broadcast from another client: {data.get('from_client', {}).get('message')}")
        elif msg_type == 'error':
            print(f"❌ Server error: {data.get('message')}")
        else:
            print(f"📥 Server message: {data}")
    
    async def run_client(self):
        """Run the advanced WebSocket client"""
        print(f"Starting WebSocket client...")
        print(f"Target server: {self.server_ip}:{self.server_port}")
        
        if not await self.connect_to_server():
            return
        
        # Start listening for messages
        listen_task = asyncio.create_task(self.listen_for_messages())
        
        # Interactive message sending
        try:
            while self.running:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Enter message (or 'quit' to exit): "
                )
                
                if message.lower() == 'quit':
                    self.running = False
                    break
                
                await self.send_message(message)
                
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        except EOFError:
            print("\nInput stream closed")
        finally:
            self.running = False
            listen_task.cancel()
            if self.websocket:
                await self.websocket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python websocket_client_advanced.py <server_ip>")
        print("Example: python websocket_client_advanced.py 192.168.1.100")
        sys.exit(1)
    
    server_ip = sys.argv[1]
    client = AdvancedWebSocketClient(server_ip)
    
    try:
        asyncio.run(client.run_client())
    except KeyboardInterrupt:
        print("\nClient stopped by user")