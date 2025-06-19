import asyncio
import websockets
import json
# import threading  # No longer needed
import sys
from datetime import datetime

class WebSocketClient:
    def __init__(self, server_ip, server_port=8765):
        self.server_ip = server_ip
        self.server_port = server_port
        self.websocket = None
        self.running = False
        
    async def connect_to_server(self):
        """Connect to the WebSocket server"""
        uri = f"ws://{self.server_ip}:{self.server_port}"
        print(f"Connecting to {uri}...")
        
        try:
            self.websocket = await websockets.connect(uri)
            self.running = True
            print("Connected successfully!")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def send_message(self, message):
        """Send message to server"""
        if self.websocket:
            try:
                msg_data = {
                    "message": message,
                    "client_timestamp": datetime.now().isoformat(),
                    "type": "client_message"
                }
                await self.websocket.send(json.dumps(msg_data))
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, cannot send message")
                self.running = False
            except Exception as e:
                print(f"Error sending message: {e}")
    
    async def listen_for_messages(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    print(f"\n--- Received from server ---")
                    print(f"Type: {data.get('type', 'unknown')}")
                    print(f"Message: {data}")
                    print("--- End of message ---\n")
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection to server closed")
            self.running = False
        except Exception as e:
            print(f"Error listening for messages: {e}")
            self.running = False
    
    async def run_client(self):
        """Run the WebSocket client"""
        if not await self.connect_to_server():
            return
        
        # Start listening for messages in background
        listen_task = asyncio.create_task(self.listen_for_messages())
        
        # Handle user input in main loop
        try:
            print("Enter message (or 'quit' to exit):")
            while self.running:
                try:
                    
                    # Use asyncio to handle input without blocking
                    message = await asyncio.get_event_loop().run_in_executor(None, input)
                    
                    if message.lower() == 'quit':
                        self.running = False
                        break
                    
                    await self.send_message(message)
                    
                except EOFError:
                    self.running = False
                    break
                except Exception as e:
                    print(f"Input error: {e}")
                    break
        finally:
            # Cleanup
            self.running = False
            listen_task.cancel()
            if self.websocket:
                await self.websocket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python websocket_client.py <server_ip>")
        print("Example: python websocket_client.py 192.168.1.100")
        sys.exit(1)
    
    server_ip = sys.argv[1]
    client = WebSocketClient(server_ip)
    
    try:
        asyncio.run(client.run_client())
    except KeyboardInterrupt:
        print("\nClient stopped by user")