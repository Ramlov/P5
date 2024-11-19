#!/bin/env python
import asyncio
import websockets
from datetime import datetime

SERVER_HOST = "192.168.1.7"
START_PORT = 21000
END_PORT = 21005


async def send_messages(port, initial_delay):
    await asyncio.sleep(initial_delay)
    uri = f"ws://{SERVER_HOST}:{port}"
    # Bind source port
    local_addr = ("192.168.1.9", port) if port else None
    async with websockets.connect(uri, local_addr=local_addr) as websocket:
        print(
            f"Connected to server on port {port} (source port: {port})")
        try:
            while True:
                send_time = datetime.utcnow()
                message = f"Hello from client on port {port} | Sent at {send_time}"
                await websocket.send(message)
                print(
                    f"Sent to server at {send_time} on port {port}: {message}")

                ack = await websocket.recv()
                receive_time = datetime.utcnow()
                print(
                    f"Received from server at {receive_time} on port {port}: {ack}")

                latency = (receive_time - send_time).total_seconds() * \
                    1000  # in milliseconds
                print(f"Latency on port {port}: {latency:.2f} ms")

                await asyncio.sleep(2)
        except websockets.exceptions.ConnectionClosedError:
            print(f"Server disconnected on port {port}")
        finally:
            print(f"Connection closed on port {port}")


async def main():
    # Create a list of tasks for each port, with an increasing initial delay
    tasks = [send_messages(port, initial_delay=2 + (port - START_PORT))
             for port in range(START_PORT, END_PORT + 1)]
    # Run all tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
