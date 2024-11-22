import asyncio
import websockets
from scapy.all import sniff
from datetime import datetime, timedelta
import threading
import json
import ntplib


class PassiveMonitoring:
    def __init__(self, field_devices, fd_locks, host="192.168.1.3", port=8765):
        """
        Initialize Passive Network Monitoring.
        :param field_devices: Dictionary to store field device data.
        :param fd_locks: Locks for thread-safe operations on field_devices.
        :param host: Host IP for the WebSocket server.
        :param port: Port for the WebSocket server.
        :param interface: Network interface for packet sniffing.
        """
        self.field_devices = field_devices
        self.fd_locks = fd_locks
        self.host = host
        self.port = port
        self.packet_data = {}  # Store packet data per connection (keyed by (src_ip, src_port))
        self.capture_thread = None  # Will be the sniffer later. Can be used to restart etc
        self.server_thread = None  # Will be the server later. Can be used to restart etc
        self.shutdown_event = threading.Event()  # Event to signal shutdown
        self.ntp_offset = self.get_ntp_offset()

    def get_ntp_offset(self):
        """
        Fetch NTP time offset to synchronize timing.
        """
        try:
            client = ntplib.NTPClient()
            response = client.request("pool.ntp.org")
            return response.offset
        except Exception as e:
            print(f"Failed to fetch NTP time: {e}")
            return 0

    def get_ntp_time(self):
        """
        Get current time synchronized with NTP (as a datetime object).
        """
        return datetime.now() + timedelta(seconds=self.ntp_offset)

    def start_packet_capture(self):
        """
        Start packet sniffing to capture Layer 3 packets (IP/TCP).
        """
        try:
            sniff(
                filter=f"tcp port {self.port}",
                prn=self.process_packet,
                store=False,
                stop_filter=lambda _: self.shutdown_event.is_set(),
            )
        except Exception as e:
            print(f"Error in packet sniffing: {e}")
        finally:
            print("Packet capture stopped.")

    def process_packet(self, packet):
        """
        Process captured packets and store them for analysis.
        """
        if packet.haslayer("IP") and packet.haslayer("TCP"):
            src_ip = packet["IP"].src
            dst_ip = packet["IP"].dst
            src_port = packet["TCP"].sport
            dst_port = packet["TCP"].dport

            print(f"Destination: {dst_ip}:{dst_port}")

            timestamp = self.get_ntp_time()  # Use NTP-synced time as datetime

            # Unique key for the field device connection
            key = (src_ip, src_port)

            # Store packet details
            packet_info = {
                "timestamp": timestamp,
                "size": len(packet),
            }

            # Initialize packet storage for this connection if not present
            if key not in self.packet_data:
                self.packet_data[key] = []

            self.packet_data[key].append(packet_info)

    def analyze_packets(self, send_time, packets):
        """
        Analyze captured packets to calculate metrics (latency and throughput).
        """
        packet_count = len(packets)
        if packet_count == 0:
            print("No packets found for this connection.")
            return {
                "packet_count": 0,
                "total_data_size": 0,
                "total_time": 0,
                "avg_latency_ms": 0,
                "throughput_kbps": 0,
            }

        total_data_size = sum(p["size"] for p in packets)
        t_last_packet = packets[-1]["timestamp"]

        # Calculate total time as the difference between the last packet and the send timestamp
        total_time = (t_last_packet - send_time).total_seconds()

        # Prevent negative total_time
        if total_time < 0:
            print("Error: Total time is negative. Check NTP synchronization.")
            total_time = 0

        # Calculate average latency per packet as total_time / packet_count
        avg_latency = total_time / packet_count if packet_count > 0 else 0

        # Calculate throughput
        throughput = total_data_size / total_time if total_time > 0 else 0
        throughput_kbps = (throughput * 8) / 1000  # Convert bytes/sec to kbps

        timestamp = self.get_ntp_time()

        return {
            "packet_count": packet_count,
            "total_data_size": total_data_size,
            "total_time": total_time,
            "avg_latency_ms": avg_latency * 1000,  # Convert to milliseconds
            "throughput_kbps": throughput_kbps,
            "last_active": timestamp
        }

    async def process_bulk_upload(self, websocket):
        """
        Handle WebSocket messages for bulk uploads and analyze metrics.
        """
        # These variables are used for cleanup if communication fails
        fd_id = None
        key = None

        try:
            async for message in websocket:
                # Extract WebSocket connection details
                src_ip, src_port = websocket.remote_address
                print(f"Field Device IP: {src_ip}:{src_port}")

                # Parse the message
                data = json.loads(message)
                fd_id = str(data.get("device_id", "Unknown"))
                send_timestamp = float(data.get("send_timestamp"))

                # Convert Timestamp
                send_time = datetime.fromtimestamp(send_timestamp)

                # Get packets for this connection
                key = (src_ip, src_port)
                packets = self.packet_data.get(key, [])

                # Analyze packets for latency and throughput
                metrics = self.analyze_packets(send_time, packets)

                status = self.classify_connection(metrics)

                # Print results
                print(f"Device ID: {fd_id}")
                print(f"Packet Count: {metrics['packet_count']}")
                print(f"Total Data Size: {metrics['total_data_size']} bytes")
                print(f"Total Time: {metrics['total_time']:.2f} seconds")
                print(f"Average Latency per Packet: {metrics['avg_latency_ms']:.2f} ms")
                print(f"Throughput: {metrics['throughput_kbps']:.2f} kbps")
                print(f"Status: {status}\n")

                # Clear packet data for this connection after processing
                if key in self.packet_data:
                    del self.packet_data[key]

                # Update the field device storage
                with self.fd_locks[fd_id]:
                    fd_info = self.field_devices.get(fd_id)
                    passive_metrics = fd_info.get('passive_metrics', {})

                    # Update the fields
                    passive_metrics['latency'] = metrics['avg_latency_ms']
                    passive_metrics['throughput'] = metrics['throughput_kbps']
                    passive_metrics['status'] = status
                    passive_metrics['last_active'] = metrics['last_active']
                    fd_info['passive_metrics'] = passive_metrics 

        except Exception as e:
            print(f"Error processing bulk upload: {e}")
            print(f"Classifying as Unavailable\n")

            status = self.classify_connection(metrics=0)

            # Update the field device storage
            with self.fd_locks[fd_id]:
                fd_info = self.field_devices.get(fd_id)
                passive_metrics = fd_info.get('passive_metrics', {})

                # Update the fields
                passive_metrics['status'] = status
                passive_metrics['last_active'] = self.get_ntp_time()
                fd_info['passive_metrics'] = passive_metrics

    def classify_connection(self, metrics):
        if metrics == 0:
            return "Unavailable"
        return "Good"

    async def start_server(self):
        """
        Start the WebSocket server and keep it running until shutdown event is set.
        """
        async with websockets.serve(self.process_bulk_upload, self.host, self.port):
            print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
            await self.wait_for_shutdown()

    async def wait_for_shutdown(self):
        """
        Coroutine that waits for the shutdown event to be set.
        """
        while not self.shutdown_event.is_set():
            await asyncio.sleep(1)

    def run_websocket_server(self):
        """
        Run the WebSocket server in a separate thread with its own event loop.
        """
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run start_server(), which handles the server setup and waiting
            loop.run_until_complete(self.start_server())
        except Exception as e:
            print(f"Error while running server: {e}")
        finally:
            loop.close()
            print("WebSocket server stopped.")

    def start(self):
        """
        Start the WebSocket server and packet capture with graceful shutdown.
        """
        # Create a shutdown event to manage graceful shutdown
        self.shutdown_event = threading.Event()

        # Run packet sniffing in a separate thread
        self.capture_thread = threading.Thread(target=self.start_packet_capture, daemon=True)
        self.capture_thread.start()

        # Run the WebSocket server in a separate thread
        self.server_thread = threading.Thread(target=self.run_websocket_server, daemon=True)
        self.server_thread.start()

    def stop(self):
        """
        Stop all ongoing operations and close the server gracefully.
        """
        print("Shutting down...")
        self.shutdown_event.set()  # Signal both threads to stop

        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join()
        if self.server_thread:
            self.server_thread.join()
        print("Shutdown complete.")


# Uncomment and adjust the following lines if you want to run this module directly
# if __name__ == "__main__":
#     monitoring = PassiveMonitoring(interface="Wi-Fi")  # Replace with your network interface name
#     monitoring.start()
#
#     # Keep the main thread alive
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("Keyboard interrupt received. Stopping...")
#         monitoring.stop()
