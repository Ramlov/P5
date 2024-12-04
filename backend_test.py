import asyncio
import websockets

async def test_backend_listener(server_ip, backend_listen_port):
    async def send_test_messages():
        uri = f"ws://{server_ip}:{backend_listen_port}"
        try:
            async with websockets.connect(uri) as websocket:
                # Send a regular focus request
                test_message_1 = "1,2,3"
                print(f"Sending message: {test_message_1}")
                await websocket.send(test_message_1)
                await asyncio.sleep(10)  # Give the server time to process
                
                # Send a 'stop' command
                test_message_2 = "stop"
                print(f"Sending message: {test_message_2}")
                await websocket.send(test_message_2)
                await asyncio.sleep(1)  # Give the server time to process
        except Exception as e:
            print(f"Test failed with exception: {e}")

    await send_test_messages()

# Parameters for the server
server_ip = "192.168.1.14"
backend_listen_port = 8000

# Run the test script
asyncio.run(test_backend_listener(server_ip, backend_listen_port))