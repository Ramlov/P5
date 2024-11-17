import asyncio
import websockets
from scapy.all import sniff, conf
from datetime import datetime
from ntplib import NTPClient
import threading
import json


class PassiveNetworkMonitoring:
    def __init__(self, host="192.168.0.129", port=8765, interface="Wi-Fi"):
        self.host = host
        self.port = port
        self.interface = interface
        self.ntp_server = "pool.ntp.org"
        self.ntp_offset = self.get_ntp_offset()
        self.packet_data = {}  # Store packet data during capture, indexed by (src_ip, src_port)
        self.capture_thread = None

    def get_ntp_offset(self):
        """
        Fetch NTP time offset to synchronize timing.
        """
        try:
            client = NTPClient()
            response = client.request(self.ntp_server)
            return response.offset
        except Exception as e:
            print(f"Failed to fetch NTP time: {e}")
            return 0

    def start_packet_capture(self):
        """
        Start packet sniffing on the specified interface using Layer 3 (IP level).
        """
        conf.use_pcap = True  # Use Layer 3 sniffing without requiring Npcap/WinPcap
        sniff(
            iface=self.interface,
            filter=f"tcp port {self.port}",
            prn=self.process_packet,
            store=False,
        )

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

    def monitor_packets(self, ntp_start_time, packets):
        """
        Analyze captured packets for latency and throughput metrics for a specific connection.
        """
        packet_count = len(packets)
        if packet_count == 0:
            return {
                "packet_count": 0,
                "total_data_size": 0,
                "total_time": 0,
                "avg_latency_ms": 0,
                "throughput_kbps": 0,
            }

        total_data_size = sum(p["size"] for p in packets)
        t_first_packet = packets[0]["timestamp"]
        t_last_packet = packets[-1]["timestamp"]

        total_time = (t_last_packet - t_first_packet).total_seconds()
        avg_latency = (t_last_packet.timestamp() - ntp_start_time) / packet_count
        throughput = total_data_size / total_time if total_time > 0 else 0
        throughput_kbps = (throughput * 8) / 1000  # Convert bytes/sec to kbps

        return {
            "packet_count": packet_count,
            "total_data_size": total_data_size,
            "total_time": total_time,
            "avg_latency_ms": avg_latency * 1000,  # Convert to milliseconds
            "throughput_kbps": throughput_kbps,
        }

    async def process_bulk_upload(self, websocket):
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

    def run(self):
        """
        Start the WebSocket server and packet capture.
        """
        # Run packet sniffing in a separate thread to avoid blocking the WebSocket server
        self.capture_thread = threading.Thread(target=self.start_packet_capture, daemon=True)
        self.capture_thread.start()

        # Start the WebSocket server using asyncio.run
        async def start_server():
            server = websockets.serve(self.websocket_handler, self.host, self.port)
            print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
            await server

        asyncio.run(start_server())


if __name__ == "__main__":
    # Instantiate and run the monitoring module
    monitoring = PassiveNetworkMonitoring()
    monitoring.run()
