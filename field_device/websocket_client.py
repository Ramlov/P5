import asyncio
import websockets
import json

async def connect_to_field_device():
    uri = "ws://localhost:3000"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")

            # Request current data from the server
            #await websocket.send("current_data")
            #current_data = await websocket.recv()
            #print("Received current data:")
            #print(current_data)

            # Request past data (e.g., for the last 15 seconds)
            await websocket.send("past_data")
            past_data = await websocket.recv()
            print("Received past data:")
            print(past_data)

            await websocket.send("all_data")
            all_data = await websocket.recv()
            print("Received all data:")
            print(all_data)

            await websocket.send("bulk_upload")
            bulk_data = await websocket.recv()
            print("Received bulk data:")
            print(bulk_data)


    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed unexpectedly.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the client
if __name__ == "__main__":
    asyncio.run(connect_to_field_device())
