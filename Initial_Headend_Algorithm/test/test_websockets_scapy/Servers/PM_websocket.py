from scapy.all import sniff, IP, TCP, Raw
import asyncio
import websockets
import threading
import json
import time
import datetime
import csv

class PassiveMonitoring:
    def __init__(self, interface='lo', target_ip="127.0.0.1", target_port=8080, bulk_log_file="bulk_upload_log_for_websocket.csv", session_log_file="session_log_for_websocket.csv"):
        self.interface = interface
        self.target_ip = target_ip
        self.target_port = target_port
        self.sessions = {}  # Track data per session (source IP and port)
        self.bulk_log_file = bulk_log_file
        self.session_log_file = session_log_file
        self.prepare_log_files()

    def prepare_log_files(self):
        """Initialize the CSV files with headers if they don’t already exist."""
        with open(self.bulk_log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow([
                    "Device ID", "Session ID", "Received Time", "Measurement Time", "Measurement Latency (ms)", "Send Time", "Send Latency (ms)", "Data"
                ])
        with open(self.session_log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow([
                    "Session ID", "Session Start", "Session End", "RTT (ms)", "Total Data (bytes)", "Throughput (bps)"
                ])

    def start_monitoring(self):
        self.capture_packets()

    def capture_packets(self):
        filter_string = f"tcp and dst host {self.target_ip} and dst port {self.target_port}"
        print(f"Starting TCP packet capture on interface {self.interface} with filter: {filter_string}")
        sniff(iface=self.interface, filter=filter_string, prn=self.process_packet, store=0)

    def process_packet(self, packet):
        if packet.haslayer(IP) and packet.haslayer(TCP):
            self.process_packet_tcp(packet)

    def process_packet_tcp(self, packet):
        tcp_flags = packet[TCP].flags

        # Generate a unique session ID using source IP and port
        src_ip = packet[IP].src
        src_port = packet[TCP].sport
        session_id = (src_ip, src_port)
        print(f"Processing packet with session ID: {session_id}")  # Print session ID

        # Fetch or initialize session data for this TCP session
        session = self.sessions.setdefault(session_id, {
            "data_transferred": 0,
            "session_start_time": None,
            "session_end_time": None,
        })

        # Calculate total packet size (including IP, TCP headers)
        packet_size = len(packet)
        session["data_transferred"] += packet_size  # Track total data size

        # Start session timing on SYN
        if tcp_flags == "S" and session["session_start_time"] is None:
            session["session_start_time"] = packet.time

        # End session timing on FIN-ACK
        elif tcp_flags == "FA" and session["session_start_time"] is not None:
            session["session_end_time"] = packet.time
            session_rtt = (session["session_end_time"] - session["session_start_time"]) * 1000  # ms
            throughput = self.calculate_throughput(session_rtt, session["data_transferred"])

            # Log the session details with associated device_id
            self.log_session(
                session_id,
                session["session_start_time"],
                session["session_end_time"],
                session_rtt,
                session["data_transferred"],
                throughput
            )

            # Reset session for next round
            del self.sessions[session_id]

    def calculate_throughput(self, rtt, data_size):
        data_size_bits = data_size * 8  # Convert bytes to bits
        rtt_seconds = rtt / 1000  # Convert ms to seconds
        return data_size_bits / rtt_seconds  # Throughput in bps

    def log_session(self, session_id, start_time, end_time, rtt, total_data, throughput):
        """Log session details to the session CSV file."""
        with open(self.session_log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                session_id,
                time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)),
                time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time)),
                round(rtt, 2), total_data, round(throughput, 2)
            ])

    def log_bulk_upload(self, device_id, session_id, received_time, measurement_time, measurement_latency, send_time, send_latency, data):
        """Log bulk upload details to the bulk upload CSV file."""
        with open(self.bulk_log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                f"{device_id:<5}",  # Align device ID
                f"{session_id:<20}",  # Align session ID
                f"{received_time.isoformat():<30}",  # Align received time
                f"{measurement_time.isoformat():<30}",  # Align measurement time
                f"{round(measurement_latency, 2):<15}",  # Align measurement latency
                f"{send_time.isoformat():<30}",  # Align send time
                f"{round(send_latency, 2):<15}",  # Align send latency
                json.dumps(data)  # Data
            ])

# WebSocket server function
async def websocket_handler(websocket, path):
    print("WebSocket connection established.")
    try:

        async for message in websocket:
            received_time = datetime.datetime.now()
            print(f"Received message from client at {received_time.isoformat()}: {message}")

            # Extract source IP and port from the WebSocket connection
            src_ip, src_port = websocket.remote_address
            session_web_id = (src_ip, src_port)
            print(f"WebSocket connection from {session_web_id}")  # Print session ID            

            # Parse the received message
            data = json.loads(message)
            if data:
                for measurement in data["data_points"]:
                    measurement_time = datetime.datetime.fromisoformat(measurement["timestamp"])
                    send_time = datetime.datetime.fromisoformat(measurement["send_timestamp"])
                    measurement_latency = (received_time - measurement_time).total_seconds() * 1000  # Convert to milliseconds
                    send_latency = (received_time - send_time).total_seconds() * 1000  # Convert to milliseconds

                    # Log the bulk upload
                    monitor.log_bulk_upload(measurement["device_id"], str(session_web_id), received_time, measurement_time, measurement_latency, send_time, send_latency, measurement)
                    
                    # Compare session IDs
                    if session_web_id in monitor.sessions:
                        print(f"Session ID {session_web_id} found in sessions")
                    else:
                        print(f"Session ID {session_web_id} not found in sessions")

            await websocket.send("Message received by the server.")
    except websockets.ConnectionClosed:
        print("WebSocket connection closed.")

async def start_websocket_server():
    server = await websockets.serve(websocket_handler, "127.0.0.1", 8080)
    print("WebSocket server running on ws://127.0.0.1:8080")
    await server.wait_closed()

def run_monitoring_with_websocket():
    global monitor
    monitor = PassiveMonitoring(interface="lo", target_ip="127.0.0.1", target_port=8080)

    monitoring_thread = threading.Thread(target=monitor.start_monitoring)
    monitoring_thread.start()

    asyncio.run(start_websocket_server())

if __name__ == "__main__":
    run_monitoring_with_websocket()