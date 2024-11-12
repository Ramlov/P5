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
        self.data_points = []  # Store data points for bulk upload
        self.bulk_upload_interval = 30  # 5 minutes interval for bulk upload
        self.data_generation_interval = 5  # Data points generated every 5 seconds
        self.last_bulk_upload_time = 0
        self.headend_ip = "ws://192.168.152.147:8765"
        self.start_time = time.time()

    async def websocket_handler(self, websocket, path):
        print(f"Device on port {self.port} connected")
        try:
            async for message in websocket:
                if message == 'all_data':
                    response_data = json.dumps(self.data_points)
                    await websocket.send(response_data)
                    print(f"Data sent to server from device {self.device_id}")
                    self.data_points.clear()  # Clear data after sending
        except websockets.exceptions.ConnectionClosedError:
            print(f"Device on port {self.port} disconnected")

    async def start_server(self):
        print(f"Starting WebSocket server on port {self.port}")
        async with websockets.serve(self.websocket_handler, "localhost", self.port):
            await asyncio.Future()  # Run indefinitely

    def run(self):
        # Run event loop for asynchronous tasks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(
            self.start_server(),
            self.periodic_data_update()
        ))

    async def periodic_data_update(self):
        """Generates new data points and performs bulk uploads at intervals."""
        while True:
            # Generate and update data
            new_data = {
                "device_id": self.device_id,
                "power_consumption": random.uniform(50.0, 150.0),
                "voltage": random.uniform(220.0, 240.0),
                "status": "online",
                "timestamp": datetime.now().isoformat()
            }

            # Add the data point to the list
            self.data_points.append(new_data)
            print(f"Data added to field device {self.device_id}\n")

            elapsed_time = time.time() - self.start_time
            if elapsed_time < 30:
                await asyncio.sleep(self.data_generation_interval)
                continue

            # Perform bulk upload if the interval has passed
            if time.time() - self.last_bulk_upload_time >= self.bulk_upload_interval and len(self.data_points) > 0:
                await self.bulk_upload()
                self.last_bulk_upload_time = time.time()

            await asyncio.sleep(self.data_generation_interval)  # Sleep before generating new data

    async def bulk_upload(self):
        """Uploads all stored data points to the headend server."""
        if self.data_points:
            send_timestamp = datetime.now().isoformat()  # Timestamp for bulk upload initiation
            for data_point in self.data_points:
                data_point["send_timestamp"] = send_timestamp  # Add send timestamp to each data point

            bulk_data = {"data_points": self.data_points}

            print(f"Device {self.device_id}: Preparing to upload bulk data at {send_timestamp}")

            try:
                async with websockets.connect(self.headend_ip) as websocket:
                    print(f"Device {self.device_id}: Connected to server at {self.headend_ip}")
                    
                    # Send the bulk data as JSON
                    await websocket.send(json.dumps(bulk_data))
                    print(f"Device {self.device_id}: Successfully sent bulk data at {send_timestamp}")

                    # Clear the data points after successful upload
                    self.data_points.clear()
            except websockets.exceptions.ConnectionClosedError:
                print(f"Device {self.device_id}: Connection closed unexpectedly.")
            except Exception as e:
                print(f"Device {self.device_id}: An error occurred during bulk upload: {e}")

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
