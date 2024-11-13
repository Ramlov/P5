#!/bin/env python
import asyncio
import websockets
from datetime import datetime
import re

SERVER_HOST = "192.168.1.4"
SERVER_PORT = 3001

async def handle_client(websocket, path):
    print("Client connected")
    try:
        async for message in websocket:
            received_time = datetime.utcnow()
            print(f"Received from client at {received_time}: {message}")

            # Extract the sequence number from the message
            seq_match = re.search(r"Seq (\d+)", message)
            if seq_match:
                seq_number = seq_match.group(1)
                print(f"Sequence Number: {seq_number}")

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