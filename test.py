import asyncio
import websockets

async def communicate():
    uri = "ws://192.168.1.14:8765"
    async with websockets.connect(uri) as websocket:
        message = "Hello from the client!"
        print(f"Sending message to server: {message}")
        await websocket.send(message)

        response = await websocket.recv()
        print(f"Received response from server: {response}")

asyncio.run(communicate())