#!/bin/env python
import asyncio
import websockets
from datetime import datetime

SERVER_HOST = "192.168.1.7"
SERVER_PORT = 3455

async def handle_client(websocket, path):
    print("Client connected")
    try:
        async for message in websocket:
            received_time = datetime.utcnow()
            print(f"Received from client at {received_time}: {message}")

            ack_message = f"Acknowledged: {message} | Received at {received_time}"
            await websocket.send(ack_message)
    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected")
    finally:
        print("Connection closed")

async def main():
    async with websockets.serve(handle_client, SERVER_HOST, SERVER_PORT):
        print(f"Server running on {SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
