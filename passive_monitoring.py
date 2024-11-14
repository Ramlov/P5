# passive_monitoring.py

import threading
import asyncio
import time
from datetime import datetime
import json

from scapy.all import sniff, IP, TCP
import websockets

class PassiveMonitoring:
    """Performs passive monitoring by capturing network traffic and handling WebSocket connections."""

    def __init__(self, field_devices, fd_locks, interface='lo', target_ip='127.0.0.1', target_port=8088):
        self.field_devices = field_devices  # Shared field devices dictionary
        self.fd_locks = fd_locks  # Locks for thread safety
        self.interface = interface
        self.target_ip = target_ip
        self.target_port = target_port
        self.stop_event = threading.Event()
        self.loop = None  # Event loop for asyncio

    def start(self):
        # Start packet capture in a separate thread
        packet_capture_thread = threading.Thread(target=self.capture_packets, daemon=True)
        packet_capture_thread.start()

        # Start WebSocket server in a separate thread
        websocket_thread = threading.Thread(target=self.run_websocket_server, daemon=True)
        websocket_thread.start()

    def capture_packets(self):
        """Captures TCP packets destined for the target IP and port."""
        filter_string = f"tcp and dst host {self.target_ip} and dst port {self.target_port}"
        print(f"Starting TCP packet capture on interface {self.interface} with filter: {filter_string}")
        sniff(iface=self.interface, filter=filter_string, prn=self.process_packet, store=0, stop_filter=self.should_stop_sniffing)

    def should_stop_sniffing(self, packet):
        """Checks if the sniffing should stop."""
        return self.stop_event.is_set()

    def process_packet(self, packet):
        if packet.haslayer(IP) and packet.haslayer(TCP):
            src_ip = packet[IP].src

            with self.fd_locks.setdefault(src_ip, threading.Lock()):
                # Initialize field device entry if not present
                fd_info = self.field_devices.get(src_ip)
                if not fd_info:
                    self.field_devices[src_ip] = {
                        'passive_metrics': {},
                        'ip_address': src_ip,
                    }
                    fd_info = self.field_devices[src_ip]

                # Initialize or get temporary data
                if 'temp_data' not in fd_info:
                    fd_info['temp_data'] = {
                        'data_transferred': 0,
                        'start_time': time.time(),
                    }

                temp_data = fd_info['temp_data']

                # Update data transferred
                packet_size = len(packet)
                temp_data['data_transferred'] += packet_size

                # Update time window if necessary
                current_time = time.time()
                elapsed_time = current_time - temp_data['start_time']
                if elapsed_time >= 10:  # For example, every 10 seconds
                    throughput = temp_data['data_transferred'] * 8 / elapsed_time  # bits per second

                    # Update passive_metrics
                    fd_info['passive_metrics']['throughput'] = throughput
                    fd_info['passive_metrics']['last_passive'] = datetime.now()

                    # Classification can be done based on throughput
                    latency = fd_info['passive_metrics'].get('latency')
                    status = self.classify_connection(latency, throughput)
                    fd_info['passive_metrics']['status'] = status

                    # Reset temp_data
                    temp_data['data_transferred'] = 0
                    temp_data['start_time'] = current_time

                    # Logging for verification
                    print(f"[{datetime.now()}] Field Device: {src_ip} | Throughput: {throughput} bps | Status: {status}")

    def classify_connection(self, latency=None, throughput=None):
        """Classify the connection based on latency and throughput."""
        if latency is None:
            return 'Unavailable'

        if latency < 200 and throughput is not None and throughput >= 500 * 1000:  # 500 kbps
            return 'Good'
        elif 200 <= latency <= 500 and throughput is not None and throughput >= 100 * 1000:  # 100 kbps
            return 'Acceptable'
        elif latency > 500 or throughput is None or throughput < 100 * 1000:
            return 'Poor'
        else:
            return 'Poor'  # Default to 'Poor' if none of the above conditions match

    def run_websocket_server(self):
        """Runs the WebSocket server to handle incoming data from field devices."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.websocket_handler, self.target_ip, self.target_port)
        print(f"WebSocket server running on ws://{self.target_ip}:{self.target_port}")
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    async def websocket_handler(self, websocket, path):
        """Handles incoming WebSocket connections."""
        print("WebSocket connection established.")
        try:
            async for message in websocket:
                received_time = datetime.now()
                # Extract source IP from the WebSocket connection
                src_ip, src_port = websocket.remote_address

                # Parse the received message
                data = json.loads(message)
                if data:
                    # Get sent timestamp from field device
                    message_timestamp_str = data.get('sent_timestamp')
                    if message_timestamp_str:
                        message_timestamp = datetime.fromisoformat(message_timestamp_str)
                        latency = (received_time - message_timestamp).total_seconds() * 1000  # milliseconds

                        with self.fd_locks.setdefault(src_ip, threading.Lock()):
                            fd_info = self.field_devices.get(src_ip)
                            if not fd_info:
                                self.field_devices[src_ip] = {
                                    'passive_metrics': {},
                                    'ip_address': src_ip,
                                }
                                fd_info = self.field_devices[src_ip]

                            # Update passive_metrics with latency
                            fd_info['passive_metrics']['latency'] = latency
                            fd_info['passive_metrics']['last_passive'] = received_time

                            # Classification can be done based on latency and throughput
                            throughput = fd_info['passive_metrics'].get('throughput')
                            status = self.classify_connection(latency, throughput)
                            fd_info['passive_metrics']['status'] = status

                            # Logging for verification
                            print(f"[{received_time}] Field Device: {src_ip} | Latency: {latency} ms | Throughput: {throughput} bps | Status: {status}")

                    else:
                        print("No timestamp in message.")
                else:
                    print("Empty message.")

        except websockets.ConnectionClosed:
            print("WebSocket connection closed.")

    def stop(self):
        """Stops the passive monitoring."""
        self.stop_event.set()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        print("Passive monitoring stopped.")
