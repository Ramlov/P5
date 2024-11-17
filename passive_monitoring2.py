import asyncio
import websockets
from scapy.all import sniff, conf
from datetime import datetime
import threading
import json
import signal


class PassiveNetworkMonitoring:
    def __init__(self, host="0.0.0.0", port=8765, interface="Ethernet"):
        """
        Initialize Passive Network Monitoring.
        :param host: Host IP for the WebSocket server.
        :param port: Port for the WebSocket server.
        :param interface: Network interface for packet sniffing.
        """
        self.host = host
        self.port = port
        self.interface = interface  # Set the network interface for sniffing
        self.packet_data = {}  # Store packet data during capture, indexed by (src_ip, src_port)
        self.capture_thread = None
        self.shutdown_event = threading.Event()  # Event to signal shutdown
        self.websockets = set()  # Track active WebSocket connections

    def start_packet_capture(self):
        """
        Start packet sniffing on the specified interface using Layer 3 (IP/TCP) on Windows.
        """
        try:
            sniff(
                iface=self.interface,                   # Use the specified interface
                filter=f"tcp port {self.port}",         # Filter packets for the specified TCP port
                prn=self.process_packet,                # Call process_packet for each packet
                store=False,                            # Do not store packets in memory
                L2socket=conf.L3socket,                 # Use Layer 3 socket instead of Layer 2
                stop_filter=lambda _: self.shutdown_event.is_set(),  # Stop when event is set
            )

        except Exception as e:
            print(f"Error in packet sniffing: {e}")
        finally:
            print("Packet capture stopped.")

    def process_packet(self, packet):
        """
        Process captured packets and store them in the appropriate bucket based on source IP and port.
        """
        if packet.haslayer('IP') and packet.haslayer('TCP'):
            src_ip = packet['IP'].src
            src_port = packet['TCP'].sport

            key = (src_ip, src_port)  # Unique identifier for this field device's connection

            # Initialize storage for this connection if not already present
            if key not in self.packet_data:
                self.packet_data[key] = []

            # Record packet details
            packet_info = {
                "timestamp": datetime.now(),
                "size": len(packet),
            }
            self.packet_data[key].append(packet_info)

    async def process_bulk_upload(self, websocket):
        """
        Handle WebSocket messages for bulk uploads and analyze metrics.
        """
        self.websockets.add(websocket)  # Track active WebSocket connections
        try:
            async for message in websocket:
                try:
                    # Extract WebSocket connection details
                    src_ip, src_port = websocket.remote_address  # Gets (IP, port) of the client
                    print(f"FD ip: {src_ip}:{src_port}\n")

                    # Parse the message
                    data = json.loads(message)
                    device_id = data.get("device_id", "Unknown")
                    send_timestamp = float(data["send_timestamp"])

                    # Get packets for this connection
                    key = (src_ip, src_port)
                    packets = self.packet_data.get(key, [])

                    print(f"Packets: {packets}\n")

                    # Monitor and analyze the packets
                    metrics = self.monitor_packets(send_timestamp, packets)

                    # Classify the connection
                    classification = self.classify_connection(
                        metrics["avg_latency_ms"], metrics["throughput_kbps"]
                    )

                    # Print the results
                    print(f"Device ID: {device_id}")
                    print(f"Metrics: {metrics}")
                    print(f"Connection Classification: {classification}\n")

                    # Clear the packet data for this connection after processing
                    if key in self.packet_data:
                        del self.packet_data[key]

                except Exception as e:
                    print(f"Error processing bulk upload: {e}")
        finally:
            self.websockets.remove(websocket)  # Remove connection when done

    async def websocket_handler(self, websocket):
        """
        Handle incoming WebSocket connections.
        """
        await self.process_bulk_upload(websocket)

    def classify_connection(self, avg_latency_ms, throughput_kbps):
        """
        Classify connection quality based on latency and throughput.
        """
        if avg_latency_ms < 100 and throughput_kbps > 500:
            return "Excellent"
        elif avg_latency_ms < 300 and throughput_kbps > 200:
            return "Good"
        else:
            return "Poor"

    async def start_server(self):
        """
        Start the WebSocket server.
        """
        async with websockets.serve(self.websocket_handler, self.host, self.port):
            print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Keep the server running

    def stop(self):
        """
        Stop all active connections and threads.
        """
        print("Shutting down...")
        self.shutdown_event.set()  # Stop packet sniffing
        for ws in self.websockets:
            asyncio.create_task(ws.close())  # Close all active WebSocket connections
        print("Shutdown complete.")

    def run(self):
        """
        Start the WebSocket server and packet capture with graceful shutdown.
        """
        # Run packet sniffing in a separate thread
        self.capture_thread = threading.Thread(target=self.start_packet_capture, daemon=True)
        self.capture_thread.start()

        # Handle shutdown signals
        def shutdown_handler(signum, frame):
            self.stop()

        signal.signal(signal.SIGINT, shutdown_handler)  # Handle CTRL+C
        signal.signal(signal.SIGTERM, shutdown_handler)  # Handle termination signal

        try:
            asyncio.run(self.start_server())
        except Exception as e:
            print(f"Error while running server: {e}")
        finally:
            self.stop()


if __name__ == "__main__":
    monitoring = PassiveNetworkMonitoring(interface="Ethernet")  # Replace with your network interface name
    monitoring.run()
