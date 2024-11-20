import threading
import time
import json
import asyncio
import websockets
import random
from datetime import datetime
import ntplib  # Added for NTP synchronization


class FieldDevice:
    def __init__(self, device_id, port):
        self.device_id = device_id
        self.port = port
        self.data_storage = []
        self.headend_url = "ws://192.168.1.7:8765"
        self.last_collected_data = time.time()
        self.datapoint_time = 5  # Interval between data generation (seconds)
        self.bulkupload_time = 500  # Interval between bulk uploads (seconds)
        self.ntp_client = ntplib.NTPClient()  # Initialize the NTP client
        self.ntp_server = "pool.ntp.org"  # Public NTP server
        self.ntp_offset = self.get_ntp_offset()

    def get_ntp_offset(self):
        """Get the offset between the local clock and NTP time."""
        try:
            response = self.ntp_client.request(self.ntp_server)
            return response.offset  # Offset in seconds
        except Exception as e:
            print(f"Failed to get NTP offset: {e}")
            return 0  # Fallback to no offset if NTP fails

    def get_ntp_timestamp(self):
        """Get the current synchronized timestamp as a UNIX timestamp."""
        return time.time() + self.ntp_offset

    async def websocket_handler(self, websocket):
        print(f"Device on port {self.port} connected")
        try:
            async for message in websocket:
                # print(f"Received from {self.port}: {message}")
                if message == "FETCH_DATA":
                    if self.data_storage:
                        response_data = json.dumps(self.data_storage)
                    else:
                        response_data = "No data available"

                    await websocket.send(response_data)
                    print(f"Data sent to server from device {self.device_id}")
                    self.data_storage.clear()  # Clear data after sending
        except websockets.exceptions.ConnectionClosedError:
            print(f"Device on port {self.port} disconnected")

    async def start_server(self):
        print(f"Starting WebSocket server on port {self.port}")
        async with websockets.serve(self.websocket_handler, "192.168.1.2", self.port):
            await asyncio.Future()  # Run forever

    def run(self):
        """Run the field device asynchronously."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(
            self.start_server(),
            self.periodic_data_update(),
        ))

    async def periodic_data_update(self):
        """Generates new data points and performs bulk uploads at intervals."""
        while True:
            # Generate and update data with device_id and timestamp
            new_data = {
                "power_consumption": random.uniform(50.0, 150.0),
                "voltage": random.uniform(220.0, 240.0),
            }

            # Add the data point to the list
            self.data_storage.append(new_data)
            print(f"Data added to field device {self.device_id}: {new_data}")

            # Perform a bulk upload if the interval is reached
            if time.time() - self.last_collected_data >= self.bulkupload_time:
                if self.data_storage:
                    await self.bulk_upload()
                self.last_collected_data = time.time()

            await asyncio.sleep(self.datapoint_time)

    async def bulk_upload(self):
        """Uploads all stored data points to the headend server."""
        if self.data_storage:
            send_timestamp = self.get_ntp_timestamp()  # Use synchronized UNIX timestamp

            bulk_data = {
                "send_timestamp": send_timestamp,  # Send the UNIX timestamp
                "device_id": self.device_id,
                "data": self.data_storage,
            }

            try:
                async with websockets.connect(self.headend_url) as websocket:
                    print(f"Device {self.device_id}: Connected to server at {self.headend_url}")
                    
                    # Send the bulk data as JSON
                    await websocket.send(json.dumps(bulk_data))
                    print(f"Device {self.device_id}: Successfully sent bulk data at {send_timestamp}")

                    # Clear the data points after successful upload
                    self.data_storage.clear()
            except websockets.exceptions.ConnectionClosedError:
                print(f"Device {self.device_id}: Connection closed unexpectedly.")
            except Exception as e:
                print(f"Device {self.device_id}: An error occurred during bulk upload: {e}")


if __name__ == "__main__":
    FD_AMOUNT = 10  # Number of field devices to simulate
    threads = []
    for id in range(FD_AMOUNT):
        port = 21000 + id
        device = FieldDevice(id, port)
        thread = threading.Thread(target=device.run)
        threads.append(thread)
        thread.start()

    print(f"Number of Field Devices: {len(threads)}")

    for thread in threads:
        thread.join()
