import threading
import time
import json
import os
import asyncio
import websockets
import random
from datetime import datetime, timedelta
from colorama import Fore, Style, init

# Initialize colorama for colorful terminal output
init(autoreset=True)

# Global print lock to ensure thread-safe printing
print_lock = threading.Lock()

# Global packet count to track total packets sent by all devices
total_packet_count = 0

class FieldDevice:
    def __init__(self, device_id, file_lock):
        self.uri = "ws://localhost:8088"  # WebSocket server IP and port 
        self.bulk_upload_interval = 15  # Bulk upload interval in seconds (Can change to any value)
        self.data_generation_interval = 5  # Data points are generated every 5 seconds (Can change to any value)
        self.packet_count = 0  # Initialize packet count
        self.device_id = device_id
        self.file_lock = file_lock
        self.last_bulk_upload_time = 0
        self.data_points = []  # Store data points to be uploaded
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

    def run(self):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Schedule periodic data updates
        loop.run_until_complete(self.periodic_data_update())

    async def periodic_data_update(self):
        """Generates new data points, writes them to a file, and performs bulk uploads at intervals."""
        while True:
            # Generate and update data
            self.data["power_consumption"] = random.uniform(50.0, 150.0)
            self.data["voltage"] = random.uniform(220.0, 240.0)
            self.data["status"] = "online"
            self.data["timestamp"] = datetime.now().isoformat()

            # Add the data point to the list
            self.data_points.append(self.data.copy())

            # Write updated data to the file
            self.write_data_to_file()

            # Perform a bulk upload defined by the interval
            if time.time() - self.last_bulk_upload_time >= self.bulk_upload_interval:  
                await self.bulk_upload()
                self.last_bulk_upload_time = time.time()

            await asyncio.sleep(self.data_generation_interval)  # Sleep between data updates

    def write_data_to_file(self):
        """Writes the current data to a JSON file."""
        with self.file_lock:
            os.makedirs("./field_device", exist_ok=True)
            with open("./field_device/field_devices_data.json", "a") as file:
                json.dump(self.data, file)
                file.write("\n")

    async def bulk_upload(self):
        """Uploads the collected data points to the WebSocket server and deletes them from the JSON file."""
        if self.data_points:
            send_timestamp = datetime.now().isoformat()  # Timestamp for bulk upload initiation
            for data_point in self.data_points:
                data_point["send_timestamp"] = send_timestamp  # Add send timestamp to each data point

            bulk_data = {
                "data_points": self.data_points
            }

            with print_lock:
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"{Style.BRIGHT}Device {self.device_id}: Preparing to upload bulk data...", flush=True)

            try:
                async with websockets.connect(self.uri) as websocket:
                    with print_lock:
                        print(f"{Fore.CYAN}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                              f"{Style.BRIGHT}Device {self.device_id}: Connected to server at {self.uri}", flush=True)
                    
                    await websocket.send(json.dumps(bulk_data))
                    global total_packet_count
                    total_packet_count += 1  # Increment global packet count
                    print(f"Total Packet Count: {total_packet_count}")

                    with print_lock:
                        print(f"{Fore.GREEN}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                              f"{Style.BRIGHT}Device {self.device_id}: Successfully sent bulk data", flush=True)
                    
                    # Clear the data points after successful upload
                    self.data_points.clear()

                    # Clear the JSON file
                    with self.file_lock:
                        with open("./field_device/field_devices_data.json", "w") as file:
                            file.write("")
            except websockets.exceptions.ConnectionClosedError:
                with print_lock:
                    print(f"{Fore.RED}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"{Style.BRIGHT}Device {self.device_id}: Connection closed unexpectedly.", flush=True)
            except Exception as e:
                with print_lock:
                    print(f"{Fore.RED}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"{Style.BRIGHT}Device {self.device_id}: An error occurred during bulk upload: {e}", flush=True)

if __name__ == '__main__':
    file_lock = threading.Lock()
    threads = []
    for id in range(1):  # Simulate 10 devices
        device = FieldDevice(id, file_lock)
        thread = threading.Thread(target=device.run)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
