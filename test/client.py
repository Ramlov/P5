#!/bin/env python
import asyncio
import websockets
from datetime import datetime

SERVER_HOST = "192.168.1.6"
SERVER_PORT = 8768

async def send_messages():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        try:
            while True:
                send_time = datetime.utcnow()
                message = f"Hello from client | Sent at {send_time}"
                await websocket.send(message)
                print(f"Sent to server at {send_time}: {message}")

                ack = await websocket.recv()
                receive_time = datetime.utcnow()
                print(f"Received from server at {receive_time}: {ack}")

                latency = (receive_time - send_time).total_seconds() * 1000  # in milliseconds
                print(f"Latency: {latency:.2f} ms")

                await asyncio.sleep(10)
        except websockets.exceptions.ConnectionClosedError:
            print("Server disconnected")
        finally:
            print("Connection closed")

if __name__ == "__main__":
    asyncio.run(send_messages())
