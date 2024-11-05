import threading
import random
import time
import json
import os

class FieldDevice(threading.Thread):
    def __init__(self, device_id, file_lock):
        super().__init__()
        self.device_id = device_id
        self.file_lock = file_lock
        self.data = {
            "device_id": self.device_id,
            "power_consumption": 0.0,
            "voltage": 0.0,
            "status": "offline"
        }
    
    def run(self):
        while True:
            # 98% chance of being online, 2% chance of being offline
            self.data["status"] = random.choices(["online", "offline"], weights=[98, 2])[0]
            
            if self.data["status"] == "online":
                self.data["power_consumption"] = round(random.uniform(50.0, 500.0), 2)  # Power in Watts
                self.data["voltage"] = round(random.uniform(220.0, 240.0), 2)  # Voltage in Volts
            else:
                # If offline, set power consumption and voltage to 0
                self.data["power_consumption"] = 0.0
                self.data["voltage"] = 0.0

            self.write_data_to_file()

            # Simulate data update every 2 seconds
            time.sleep(2)
    
    def write_data_to_file(self):
        with self.file_lock:
            # Create the directory if it doesn't exist
            os.makedirs("./field_device", exist_ok=True)
            with open("./field_device/field_devices_data.json", "a") as file:
                json.dump(self.data, file)
                file.write("\n")  # Each data entry is saved in a new line

def emulate_field_devices(num_devices):
    file_lock = threading.Lock()

    devices = []
    for i in range(num_devices):
        device = FieldDevice(i, file_lock)
        devices.append(device)

    for device in devices:
        device.start()

# Start the emulation with n field devices
if __name__ == "__main__":
    n = 5  # For example, emulate 5 field devices
    emulate_field_devices(n)
