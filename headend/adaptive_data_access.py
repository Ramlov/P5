# adaptive_data_access.py

import threading
import time
from datetime import datetime, timedelta
import asyncio
import websockets

class AdaptiveDataAccess:
    """Adjusts data access strategies based on network metrics and backend requests."""

    def __init__(self, field_devices, fd_locks):
        self.field_devices = field_devices
        self.fd_locks = fd_locks
        self.focused_fd_ids = None  # None means no specific focus
        self.stop_event = threading.Event()
        self.lock = threading.Lock()  # Lock to protect access to focused_fd_ids
        self.ada_wait_time = 15000 #Time to wait in seconds until a fd has generated a new data point

    def run(self):
        while not self.stop_event.is_set():
            with self.lock:
                current_focus = self.focused_fd_ids.copy() if self.focused_fd_ids else None

            if current_focus:
                # Focus on the requested FDs
                for fd_id in current_focus:
                    if self.stop_event.is_set():
                        break
                    self.process_fd(fd_id)
            else:
                # Process FDs based on twhe adaptive data access logic
                fd_list = self.get_fds_to_fetch()
                print(f"Field Device Sorted list: {fd_list}\n")
                if fd_list:
                    for fd_id in fd_list:
                        if self.stop_event.is_set():
                            break
                        self.process_fd(fd_id)
                else:
                    # No FDs need fetching at this time
                    print(f"No Current Field Devices that fit ADA Criteria\n")

            time.sleep(5)  #

    def get_fds_to_fetch(self):
        """Identify FDs that are 'available' and need data fetching."""
        available_fds = []
        current_time = datetime.now()

        for fd_id, fd_info in self.field_devices.items(): #Key is fd_id and fd_info is the value is manager.dict
            with self.fd_locks[fd_id]:
                # Determine overall availability
                is_available = self.is_fd_available(fd_id, fd_info)

                # Get 'last_fetched' timestamp
                last_fetched_str = fd_info.get('last_data_received')
                if last_fetched_str:
                    last_fetched = datetime.fromisoformat(last_fetched_str)
                else:
                    last_fetched = datetime.min  # Treat as if never fetched

                time_since_last_fetched = current_time - last_fetched
                #print(f"Time Since Field Device {fd_id} fetch: {time_since_last_fetched}\n")

                if is_available and time_since_last_fetched >= timedelta(seconds=self.ada_wait_time):
                    available_fds.append((fd_id, fd_info, is_available, last_fetched))

        if not available_fds:
            return []

        # Sort the list by last_fetched (oldest first) and sub-classification
        # Sub-classification priority: 'Good' > 'Acceptable' > 'Poor'
        classification_priority = {'Good': 1, 'Acceptable': 2, 'Poor': 3, None: 4}

        available_fds.sort(key=lambda x: (x[3], classification_priority.get(x[2], 4)))

        # Return the list of FD IDs in order
        return [fd_id for fd_id, _, _, _ in available_fds]

    def process_fd(self, fd_id):
        """Process a single FD by attempting to fetch data."""
        fd_info = self.field_devices.get(fd_id)

        # Check if the fd information actually exists (Ensure)
        if not fd_info:
            print(f"FD {fd_id} not found in field_devices.\n")
            return
        
        # Look at classification again. NM runs in background and might have new info.
        with self.fd_locks[fd_id]:
            is_available = self.is_fd_available(fd_id, fd_info)

        if not is_available:
            print(f"Field device {fd_id} is marked as Unavailable\n")
            return

        success = asyncio.run(self.fetch_data_from_fd(fd_id, fd_info))
        with self.fd_locks[fd_id]:
            if success:
                # Update 'last_data_received' timestamp
                fd_info['last_data_received'] = datetime.now().isoformat()
            else:
                # Label the FD as 'Unavailable' in active metrics
                if 'active_metrics' not in fd_info: #This should not be an issue. Only to ensure correct setup.
                    fd_info['active_metrics'] = {}
                fd_info['active_metrics']['status'] = 'Unavailable'

    def is_fd_available(self, fd_id, fd_info):
        # Determine if FD is available based on active and passive status
        # For now, only active status is considered
        # Available if status is 'Good', 'Acceptable', 'Poor', or None

        # Get classification from active monitoring (and make space for passive monitoring)
        active_status = fd_info.get('active_metrics', {}).get('status')
        # Placeholder for passive status
        passive_status = fd_info.get('passive_metrics', {}).get('status')

        available_statuses = ['Good', 'Acceptable', 'Poor'] #Tilføj none til listen hvis ADA skal køre uden nm ranking
        return active_status in available_statuses

    async def fetch_data_from_fd(self, fd_id, fd_info):
        """Fetch data from the FD using WebSockets."""
        # This function can be used both in backend focus and general cycle
        ip_address = fd_info['ip_address']
        port = fd_info.get('port', 80)
        uri = f"ws://{ip_address}:{port}"

        try:
            async with websockets.connect(uri) as websocket:
                # Send a request to fetch data
                request_message = 'FETCH_DATA'
                await websocket.send(request_message)

                # Wait for a response
                response = await websocket.recv()
                # Process the response as needed
                # For now, we assume any response means success

                print(f"Successfully fetched data from FD {fd_id} at {ip_address}:{port}\n")
                return True

        except Exception as e:
            print(f"Failed to fetch data from FD {fd_id} - {e} at {ip_address}:{port}\n")
            return False

    def focus_on_fds(self, fd_ids):
        # Start focusing on the specified FDs
        with self.lock:
            self.focused_fd_ids = fd_ids
        print(f"Adaptive Data Access is now focusing on FDs: {fd_ids}\n")

    def stop_backend_focus(self):
        # Stop focusing on specific FDs and resume normal operation
        with self.lock:
            self.focused_fd_ids = None
        print("Adaptive Data Access has stopped focusing on specific FDs and will resume normal operation.\n")

    def stop(self):
        # Stop the entire Adaptive Data Access module
        self.stop_event.set()
        print("Adaptive Data Access module is stopping.\n")
