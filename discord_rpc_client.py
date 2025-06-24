#!/usr/bin/env python3
"""
Discord RPC WebSocket Client
Connects to Discord RPC service running on localhost:6463
"""

import asyncio
import json
import websockets
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DiscordRPCClient:
    def __init__(self, host='localhost', port=6463):
        self.host = host
        self.port = port
        self.websocket = None
        self.url = f"ws://{host}:{port}"
        
    async def connect(self):
        """Connect to the Discord RPC WebSocket"""
        try:
            logger.info(f"Connecting to {self.url}")
            self.websocket = await websockets.connect(self.url)
            logger.info("Connected successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def listen(self):
        """Listen for messages from the Discord RPC service"""
        if not self.websocket:
            logger.error("Not connected. Call connect() first.")
            return
            
        try:
            async for message in self.websocket:
                logger.info(f"Received: {message}")
                
                # Parse the JSON message
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    logger.error(f"Raw message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error while listening: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages from Discord RPC"""
        cmd = data.get('cmd')
        evt = data.get('evt')
        
        if evt == 'READY':
            logger.info("Discord RPC is ready!")
            logger.info(f"User: {data['data']['user']['username']}")
            logger.info(f"Config: {data['data']['config']}")
            
            # You can send commands here after receiving READY
            # await self.send_command({"cmd": "GET_GUILDS"})
            
        elif cmd == 'DISPATCH':
            logger.info(f"Dispatch event: {evt}")
            logger.info(f"Data: {json.dumps(data['data'], indent=2)}")
        else:
            logger.info(f"Unknown message type - CMD: {cmd}, EVT: {evt}")
    
    async def send_command(self, command):
        """Send a command to Discord RPC"""
        if not self.websocket:
            logger.error("Not connected. Call connect() first.")
            return
            
        try:
            message = json.dumps(command)
            await self.websocket.send(message)
            logger.info(f"Sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
    
    async def send_activity_update(self, activity):
        """Send activity update (Rich Presence)"""
        command = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": 12345,  # Process ID (can be any number)
                "activity": activity
            },
            "nonce": "activity-update"
        }
        await self.send_command(command)
    
    async def close(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Connection closed")

async def main():
    """Main function to demonstrate the Discord RPC client"""
    client = DiscordRPCClient()
    
    # Connect to Discord RPC
    if not await client.connect():
        return
    
    # Start listening for messages
    try:
        await client.listen()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await client.close()

async def test_commands():
    """Test function to send some commands"""
    client = DiscordRPCClient()
    
    if not await client.connect():
        return
        
    try:
        # Listen for the READY event first
        async for message in client.websocket:
            data = json.loads(message)
            if data.get('evt') == 'READY':
                logger.info("Received READY, now sending test commands...")
                break
        
        # Send some test commands
        await client.send_command({"cmd": "GET_GUILDS"})
        await asyncio.sleep(1)
        
        await client.send_command({"cmd": "GET_CHANNELS", "args": {"guild_id": None}})
        await asyncio.sleep(1)
        
        # Set a rich presence activity
        activity = {
            "details": "Testing Discord RPC",
            "state": "Via WebSocket",
            "assets": {
                "large_image": "large_image_key",
                "large_text": "Large image tooltip",
                "small_image": "small_image_key",
                "small_text": "Small image tooltip"
            }
        }
        await client.send_activity_update(activity)
        
        # Listen for responses
        timeout = 10  # seconds
        try:
            await asyncio.wait_for(client.listen(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.info(f"Finished listening after {timeout} seconds")
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    print("Discord RPC WebSocket Client")
    print("1. Basic connection and listening")
    print("2. Test commands")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(test_commands())
    else:
        asyncio.run(main())
