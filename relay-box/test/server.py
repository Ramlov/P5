#!/bin/env python
import asyncio
import websockets
from datetime import datetime

START_PORT = 20000
END_PORT = 20005


async def handle_client(websocket, path, port):
    print(f"Client connected on port {port}")
    try:
        async for message in websocket:
            receive_time = datetime.utcnow()
            print(f"Received from client on port {port} at {receive_time}: {message}")

            # Send an acknowledgment message back to the client
            ack_message = f"ACK from server on port {port} | Received at {receive_time}"
            await websocket.send(ack_message)
            print(f"Sent to client on port {port}: {ack_message}")
    except websockets.exceptions.ConnectionClosedError:
        print(f"Client disconnected on port {port}")
    finally:
        print(f"Connection closed on port {port}")


async def start_server(port):
    print(f"Starting server on port {port}")
    async with websockets.serve(lambda ws, path: handle_client(ws, path, port), "0.0.0.0", port):
        await asyncio.Future()  # Keep the server running indefinitely


async def main():
    # Create and start servers on each port from START_PORT to END_PORT
    servers = [start_server(port) for port in range(START_PORT, END_PORT + 1)]
    await asyncio.gather(*servers)


if __name__ == "__main__":
    asyncio.run(main())