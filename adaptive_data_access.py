# adaptive_data_access.py

import threading
import time
from datetime import datetime

class AdaptiveDataAccess:
    """Adjusts data access strategies based on network metrics and backend requests."""

    def __init__(self, field_devices, fd_locks):
        self.field_devices = field_devices
        self.fd_locks = fd_locks
        self.focused_fd_ids = None  # None means no specific focus
        self.stop_event = threading.Event()
        self.lock = threading.Lock()  # Lock to protect access to focused_fd_ids

    def run(self):
        while not self.stop_event.is_set():
            with self.lock:
                current_focus = self.focused_fd_ids.copy() if self.focused_fd_ids else None

            if current_focus:
                # Focus on the requested FDs
                for fd_id in current_focus:
                    self.process_fd(fd_id)
                    if self.stop_event.is_set():
                        break
            else:
                # Process FDs starting from the oldest last_data_received
                sorted_fds = sorted(
                    self.field_devices.items(),
                    key=lambda item: item[1].get('last_data_received') or datetime.min
                )
                for fd_id, fd_info in sorted_fds:
                    self.process_fd(fd_id)
                    if self.stop_event.is_set():
                        break
            time.sleep(1)  # Adjust as needed

    def process_fd(self, fd_id):
        fd_info = self.field_devices.get(fd_id)
        if not fd_info:
            print(f"FD {fd_id} not found in field_devices.")
            return

        # Implement data access logic here
        # For example, initiate data retrieval from the FD
        with self.fd_locks[fd_id]:
            print(f"Adaptive Data Access processing FD {fd_id}")
            # Update 'last_data_received' timestamp
            fd_info['last_data_received'] = datetime.now().isoformat()
            # Additional processing as needed

    def focus_on_fds(self, fd_ids):
        # Start focusing on the specified FDs
        with self.lock:
            self.focused_fd_ids = fd_ids
        print(f"Adaptive Data Access is now focusing on FDs: {fd_ids}")

    def stop_backend_focus(self):
        # Stop focusing on specific FDs and resume normal operation
        with self.lock:
            self.focused_fd_ids = None
        print("Adaptive Data Access has stopped focusing on specific FDs and will resume normal operation.")

    def stop(self):
        # Stop the entire Adaptive Data Access module
        self.stop_event.set()
        print("Adaptive Data Access module is stopping.")
