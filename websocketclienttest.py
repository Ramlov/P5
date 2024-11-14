import asyncio
import websockets

async def echo(websocket, path):
    print("Client connected")
    try:
        async for message in websocket:
            print(f"Received message from client: {message}")
            response = f"Server received: {message}"
            await websocket.send(response)
            print(f"Sent response to client: {response}")
    except websockets.ConnectionClosed as e:
        print("Client disconnected")

async def main():
    server = await websockets.serve(echo, "192.168.1.14", 8765)
    print("WebSocket server started on ws://192.168.1.14:8765")
    await server.wait_closed()

asyncio.run(main())