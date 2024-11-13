import threading
import time
import json
import asyncio
import websockets
import random
from datetime import datetime, timedelta

class FieldDevice:
    def __init__(self, device_id, port):
        self.device_id = device_id
        self.port = port
        self.data_storage = []
        self.headend_ip = "192.168.152.1.14"
        self.last_collected_data = time.time()
        self.datapoint_time = 5  # 5 seconds
        self.bulkupload_time = 120


    async def websocket_handler(self, websocket):
        print(f"Device on port {self.port} connected")
        try:
            async for message in websocket:
                response_data = ''
                print(f"Received from {self.port}: ")

                if message == 'all_data':
                    response_data = json.dumps(self.data_storage)
                    self.data_storage.clear()  # Remove data after sending

                await websocket.send(response_data)
        except websockets.exceptions.ConnectionClosedError:
            print(f"Device on port {self.port} disconnected")

    async def start_server(self):
        print(f"Starting WebSocket server on port {self.port}")
        async with websockets.serve(self.websocket_handler, "192.168.1.2", self.port):
            await asyncio.Future()  # Run forever

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(
            self.start_server(),
            self.periodic_data_update()
        ))

    async def periodic_data_update(self):
        while True:
            new_data = {
                "device_id": self.device_id,
                "power_consumption": random.uniform(50.0, 150.0),
                "voltage": random.uniform(220.0, 240.0),
                "status": "online",
                "timestamp": datetime.now().isoformat()
            }
            self.data_storage.append(new_data)
            print(f"Data added to field device {self.device_id}\n")

            if time.time() - self.last_collected_data >= self.bulkupload_time:  # 5 minutes
                if self.data_storage:
                    await self.bulk_upload()
                    self.data_storage.clear()
                self.last_collected_data = time.time()

            await asyncio.sleep(self.datapoint_time)

    async def bulk_upload(self):
        uri = "ws://{self.headend_ip}"
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to headend at url: {uri}")
                await websocket.send(json.dumps(self.data_storage))
                print("Successfully sent bulk data")
        except websockets.exceptions.ConnectionClosedError:
            print("Connection closed unexpectedly.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    FD_AMOUNT = 10
    threads = []
    for id in range(FD_AMOUNT):
        port = 3000 + id
        device = FieldDevice(id, port)
        thread = threading.Thread(target=device.run)
        threads.append(thread)
        thread.start()

    print(f"Number of Field Devices: {len(threads)}")

    for thread in threads:
        thread.join()
