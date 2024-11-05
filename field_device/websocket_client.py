import asyncio
import websockets

async def websocket_client():
    uri = "ws://localhost:8765"  # Update this URI if your server runs elsewhere
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to the server. Press Enter to request data from now and the last 15 seconds.")
            while True:
                # Wait for user input to request data
                input("Press Enter to receive data from now and the last 15 seconds...")
                await websocket.send("past_data")  # Sending request for data
                response = await websocket.recv()   # Receive response
                print("Data (now and last 15 seconds):", response)

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Start the WebSocket client
if __name__ == "__main__":
    asyncio.run(websocket_client())
