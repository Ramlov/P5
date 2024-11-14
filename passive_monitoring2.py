# passive_monitoring.py

import asyncio
import threading
import time
from datetime import datetime
import json

import websockets

class PassiveMonitoring:
    """Performs passive monitoring by handling bulk uploads from field devices over WebSocket."""

    def __init__(self, field_devices, fd_locks, target_ip='0.0.0.0', target_port=8088):
        self.field_devices = field_devices  # Shared field devices dictionary
        self.fd_locks = fd_locks  # Locks for thread safety
        self.target_ip = target_ip
        self.target_port = target_port
        self.stop_event = threading.Event()
        self.loop = None  # Event loop for asyncio

    def start(self):
        # Start WebSocket server in a separate thread
        websocket_thread = threading.Thread(target=self.run_websocket_server, daemon=True)
        websocket_thread.start()

    def run_websocket_server(self):
        """Runs the WebSocket server to handle incoming data from field devices."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.websocket_handler, self.target_ip, self.target_port)
        print(f"Passive Monitoring WebSocket server running on ws://{self.target_ip}:{self.target_port}")
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    async def websocket_handler(self, websocket, path):
        """Handles incoming WebSocket connections from field devices."""
        try:
            # Extract source IP and port from the WebSocket connection
            src_ip, src_port = websocket.remote_address
            session_id = (src_ip, src_port)
            #print(f"WebSocket connection established from {session_id}")

            # Initialize variables for network metrics
            total_data_received = 0  # in bytes
            start_time = time.time() # This marks the time when the packets have been processed and received on the application layer
            latency_samples = []
            device_id = None  # Will be set upon receiving the first message

            async for message in websocket:
                print(f"Message received: {message}\n")
                received_time = datetime.now()
                message_size = len(message)
                total_data_received += message_size  # Accumulate total data received

                # Parse the received message
                data = json.loads(message)
                if data:
                    # Extract device_id from the message
                    device_id = data.get('device_id')
                    if not device_id:
                        print(f"No device_id in message from {session_id}. Ignoring message.")
                        continue  # Skip processing this message

                    # Check if device_id exists in field_devices
                    if device_id not in self.field_devices:
                        print(f"Device ID {device_id} not found in field_devices. Ignoring message from {session_id}.")
                        continue  # Skip processing this message

                    # Assume the message contains a 'timestamp' field indicating when it was sent
                    message_timestamp_str = data.get('timestamp')
                    if message_timestamp_str:
                        message_timestamp = datetime.fromisoformat(message_timestamp_str)
                        latency = (received_time - message_timestamp).total_seconds() * 1000  # milliseconds
                        latency_samples.append(latency)
                    else:
                        print(f"No timestamp in message from {session_id}")
                else:
                    print(f"Empty message received from {session_id}")

            # Bulk upload finished or connection closed
        except websockets.ConnectionClosedError:
            print(f"WebSocket connection closed with {session_id}")

        except Exception as e:
            print(f"Error handling connection with {session_id}: {e}")

        finally:
            # Close the connection
            await websocket.close()
            end_time = time.time()
            total_time = end_time - start_time  # in seconds

            # Only update metrics if device_id is known and exists in field_devices
            if device_id and device_id in self.field_devices:
                # Calculate network metrics
                throughput = (total_data_received * 8) / total_time if total_time > 0 else 0  # bits per second
                avg_latency = sum(latency_samples) / len(latency_samples) if latency_samples else None

                # Classify the connection
                status = self.classify_connection(avg_latency, throughput)

                # Update passive_metrics in the shared field_devices dictionary
                self.update_passive_metrics(device_id, avg_latency, throughput, status)

                # Logging for verification
                print(f"Session with {session_id} (Device ID: {device_id}) ended.")
                print(f"Total data received: {total_data_received} bytes")
                print(f"Total time: {total_time:.2f} seconds")
                print(f"Throughput: {throughput:.2f} bps")
                print(f"Average Latency: {avg_latency:.2f} ms" if avg_latency is not None else "Latency: N/A")
                print(f"Status: {status}")
            else:
                print(f"No valid device_id was received from {session_id}. Metrics not updated.")

    def classify_connection(self, latency, throughput):
        """Classify the connection based on latency and throughput."""
        if latency is None:
            return 'Unavailable'

        if latency < 200 and throughput >= 500 * 1000:  # 500 kbps
            return 'Good'
        elif 200 <= latency <= 500 and throughput >= 100 * 1000:  # 100 kbps
            return 'Acceptable'
        elif latency > 500 or throughput < 100 * 1000:
            return 'Poor'
        else:
            return 'Poor'  # Default to 'Poor' if none of the above conditions match

    def update_passive_metrics(self, device_id, latency, throughput, status):
        """Update the passive_metrics for the field device."""
        timestamp = datetime.now()
        try:
            with self.fd_locks[device_id]:
                fd_info = self.field_devices[device_id]
                fd_info['passive_metrics'] = {
                    'latency': latency,
                    'throughput': throughput,
                    'status': status,
                    'last_passive': timestamp,
                }
        except Exception as e:
            print(f"Error Updating fd_info: {e}\n")

    def stop(self):
        """Stops the passive monitoring."""
        self.stop_event.set()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        print("Passive monitoring stopped.")
