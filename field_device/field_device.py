import threading
import time
import json
import os
import asyncio
import websockets
import random
from datetime import datetime, timedelta

class FieldDevice:
    def __init__(self, device_id, file_lock, port):
        super().__init__()
        self.device_id = device_id
        self.file_lock = file_lock
        self.last_collected_data = 0
        self.port = port
        self.data = {
            "device_id": self.device_id,
            "power_consumption": 0.0,
            "voltage": 0.0,
            "status": "offline",
            "region": self.assign_region(),
            "timestamp": datetime.now().isoformat()
        }

    def assign_region(self):
        if 0 <= self.device_id <= 9:
            return "A1"
        elif 10 <= self.device_id <= 19:
            return "A2"
        elif 20 <= self.device_id <= 29:
            return "A3"
        return "Unknown"
    
    async def websocket_handler(self, websocket, path):
        print(f"Device on port {self.port} connected")
        try:
            async for message in websocket:
                data = ''
                print(f"Received from {self.port}: {message}")
                print("Case Matched: " + message)

                match message:
                    case 'past_data':
                        data = self.get_past_data(20)
                        self.last_collected_data = time.time()

                await websocket.send(f"{data}")
        except websockets.exceptions.ConnectionClosedError:
            print(f"Device on port {self.port} disconnected")

    async def start_server(self):
        print(f"Starting WebSocket server on port {self.port}")
        async with websockets.serve(self.websocket_handler, "localhost", self.port):
            await asyncio.Future()  # Run forever

    def run(self):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)  # Set this loop as the current one for the thread
        # Schedule both the WebSocket server and the periodic_data_update to run concurrently
        loop.run_until_complete(asyncio.gather(
            self.start_server(),
            self.periodic_data_update()
        ))

    async def periodic_data_update(self):
        while True:
            self.data["power_consumption"] = random.uniform(50.0, 150.0)  # Example random data
            self.data["voltage"] = random.uniform(220.0, 240.0)
            self.data["status"] = "online"

            if time.time() - self.last_collected_data >= 360: # 6 minutes
                self.bulk_upload()
                self.last_collected_data = time.time()
            
            # Write updated data to the file
            self.write_data_to_file()
            await asyncio.sleep(5)

    def write_data_to_file(self):
        self.data["timestamp"] = datetime.now().isoformat()  # Update timestamp before writing
        with self.file_lock:
            os.makedirs("./field_device", exist_ok=True)
            with open("./field_device/field_devices_data.json", "a") as file:
                json.dump(self.data, file)
                file.write("\n")

    def get_past_data(self, seconds):
        current_time = time.time()
        past_data = []
        with open("./field_device/field_devices_data.json", "r") as file:
            for line in file:
                data = json.loads(line)
                if data["device_id"] == self.device_id:
                    timestamp = datetime.fromisoformat(data['timestamp']).timestamp()
                    if current_time - timestamp <= seconds:
                        past_data.append(data)
        return past_data

    async def bulk_upload(self):
        cutoff_time = datetime.now() - timedelta(minutes=6)
        bulk_data = []
        with open("./field_device/field_devices_data.json", "r") as file:
            for line in file:
                data = json.loads(line)
                if data["device_id"] == self.device_id:
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if timestamp >= cutoff_time:
                        bulk_data.append(data)
        print(f"Bulk uploading all data for device {self.device_id} from the last 6 minutes...")
        
        uri = "ws://localhost:3000" # IP to headend
        try:
            with websockets.connect(uri) as websocket:
                print(f"Connected to headend at url: {uri}")
                print("Sending bulk data...")
                await websocket.send(bulk_data)
                print("Successfully sent bulk data")
    
        except websockets.exceptions.ConnectionClosedError:
            print("Connection closed unexpectedly.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    RANGE_START = 0
    file_lock = threading.Lock()
    threads = []
    for id in range(RANGE_START, RANGE_START + 10):
        port = 3000 + id  # Generates a port based on the ID
        device = FieldDevice(id, file_lock, port)
        thread = threading.Thread(target=device.run)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
