import threading
import random
import time
import json
import os
import asyncio
import websockets
from datetime import datetime, timedelta

class FieldDevice(threading.Thread):
    def __init__(self, device_id, file_lock):
        super().__init__()
        self.device_id = device_id
        self.file_lock = file_lock
        self.data = {
            "device_id": self.device_id,
            "power_consumption": 0.0,
            "voltage": 0.0,
            "status": "offline",
            "region": self.assign_region(),
            "timestamp": datetime.now().isoformat()
        }

    def assign_region(self):
        if 0 <= self.device_id <= 10:
            return "A1"
        elif 11 <= self.device_id <= 22:
            return "A2"
        elif 23 <= self.device_id <= 32:
            return "A3"
        return "Unknown"

    def run(self):
        while True:
            self.data["status"] = random.choices(["online", "offline"], weights=[98, 2])[0]
            if self.data["status"] == "online":
                self.data["power_consumption"] = round(random.uniform(50.0, 500.0), 2)
                self.data["voltage"] = round(random.uniform(220.0, 240.0), 2)
            else:
                self.data["power_consumption"] = 0.0
                self.data["voltage"] = 0.0
            self.data["timestamp"] = datetime.now().isoformat()
            self.write_data_to_file()
            time.sleep(2)

    def write_data_to_file(self):
        with self.file_lock:
            os.makedirs("./field_device", exist_ok=True)
            with open("./field_device/field_devices_data.json", "a") as file:
                json.dump(self.data, file)
                file.write("\n")

async def websocket_handler(websocket, path):
    last_request_time = time.time()
    try:
        while True:
            request = await websocket.recv()
            last_request_time = time.time()  # Update request time

            if request == "current_data":
                data = get_current_data()
                await websocket.send(json.dumps(data))

            elif request == "past_data":
                data = get_past_data(15)
                await websocket.send(json.dumps(data))

            # Check if no request is made for 6 minutes
            if time.time() - last_request_time > 360:
                bulk_upload()
                last_request_time = time.time()  # Reset the timer

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    except Exception as e:
        print(f"Error in websocket_handler: {e}")

def get_current_data():
    with open("./field_device/field_devices_data.json", "r") as file:
        lines = file.readlines()
        if lines:
            return json.loads(lines[-1])
    return {}

def get_past_data(seconds):
    current_time = time.time()
    past_data = []
    with open("./field_device/field_devices_data.json", "r") as file:
        for line in file:
            data = json.loads(line)
            timestamp = datetime.fromisoformat(data['timestamp']).timestamp()
            if current_time - timestamp <= seconds:
                past_data.append(data)
    return past_data

def bulk_upload():
    cutoff_time = datetime.now() - timedelta(minutes=6)
    bulk_data = []
    with open("./field_device/field_devices_data.json", "r") as file:
        for line in file:
            data = json.loads(line)
            timestamp = datetime.fromisoformat(data['timestamp'])
            if timestamp >= cutoff_time:
                bulk_data.append(data)
    print("Bulk uploading all field device data from the last 6 minutes...")
    print(bulk_data)  # Replace this with actual upload logic

def emulate_field_devices(num_devices):
    file_lock = threading.Lock()
    devices = []
    for i in range(num_devices):
        device = FieldDevice(i, file_lock)
        devices.append(device)

    for device in devices:
        device.start()

# Start WebSocket server
async def start_server():
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    n = 5  # For example, emulate 5 field devices
    emulate_field_devices(n)
    asyncio.run(start_server())
