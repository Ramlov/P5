from scapy.all import sniff, IP, TCP, Raw
import asyncio
import websockets
import threading
import json
import time
import datetime
import csv
import sqlite3
from queue import Queue

class PassiveMonitoring:
    def __init__(self, interface='lo', target_ip="127.0.0.1", target_port=8088, db_file="monitoring_data.db"):
        self.interface = interface
        self.target_ip = target_ip
        self.target_port = target_port
        self.sessions = {}  # Track data per session (source IP and port)
        self.db_file = db_file
        self.queue = Queue()  # Queue to pass data between threads
        self.prepare_database()

    def prepare_database(self):
        """Initialize the SQLite database with tables if they don’t already exist."""
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_upload_log (
                device_id TEXT,
                session_id TEXT,
                received_time TEXT,
                packet_size INTEGER,
                measurement_time TEXT,
                measurement_latency REAL,
                send_time TEXT,
                send_latency REAL,
                send_throughput REAL,
                classification TEXT,
                data TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_log (
                session_id TEXT,
                session_start TEXT,
                session_end TEXT,
                rtt REAL,
                total_data INTEGER,
                throughput REAL
            )
        ''')
        self.conn.commit()

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
        #print(f"Processing packet with session ID: {session_id}")  # Print session ID

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
            self.queue.put((
                session_id,
                session["session_start_time"],
                session["session_end_time"],
                session_rtt,
                session["data_transferred"],
                throughput
            ))

            # Reset session for next round
            del self.sessions[session_id]

    def calculate_throughput(self, latency, data_size):
        data_size_bits = data_size * 8  # Convert bytes to bits
        latency_seconds = latency / 1000  # Convert ms to seconds
        return data_size_bits / latency_seconds  # Throughput in bps

    def log_bulk_upload(self, device_id, session_id, received_time, packet_size, measurement_time, measurement_latency, send_time, send_latency, throughput, classification, data):
        """Log bulk upload details to the bulk upload SQLite database."""
        self.cursor.execute('''
            INSERT INTO bulk_upload_log (device_id, session_id, received_time, packet_size, measurement_time, measurement_latency, send_time, send_latency, send_throughput, classification, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_id,
            str(session_id),
            received_time.isoformat(),
            packet_size,
            measurement_time.isoformat(),
            round(measurement_latency, 2),
            send_time.isoformat(),
            round(send_latency, 2),
            round(throughput, 2),
            classification,
            json.dumps(data)
        ))
        self.conn.commit()

    def classify_connection(self, latency, throughput):
        """Classify the connection based on latency, and throughput."""
        if latency is None:
            return 'Unavailable'

        if latency < 200 and throughput is not None and throughput >= 500:
            return 'Good'
        elif 200 <= latency <= 500  and throughput is not None and throughput >= 100:
            return 'Acceptable'
        elif latency > 500 or throughput is None or throughput < 100:
            return 'Poor'
        else:
            return 'Poor'  # Default to 'Poor' if none of the above conditions match

    def process_queue(self):
        """Process the queue and log sessions to the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        while True:
            session_data = self.queue.get()
            if session_data is None:
                break
            self.log_session_with_connection(cursor, *session_data)
        conn.close()

    def log_session_with_connection(self, cursor, session_id, start_time, end_time, rtt, total_data, throughput):
        """Log session details to the session SQLite database using a specific cursor."""
        cursor.execute('''
            INSERT INTO session_log (session_id, session_start, session_end, rtt, total_data, throughput)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(session_id),
            time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)),
            time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time)),
            round(rtt, 2),
            total_data,
            round(throughput, 2)
        ))
        cursor.connection.commit()

# WebSocket server function
async def websocket_handler(websocket):
    print("WebSocket connection established.")
    try:

        async for message in websocket:
            received_time = datetime.datetime.now()
            print(f"Received message from client at {received_time.isoformat()}: {message}")

            # Extract source IP and port from the WebSocket connection
            src_ip, src_port = websocket.remote_address
            session_web_id = (src_ip, src_port)
            print(f"WebSocket connection from {session_web_id}")  # Print session ID            
            

            packet_size = len(message)
            print(f"Packet size: {packet_size} bytes")

            # Parse the received message
            data = json.loads(message)
            if data:
                for measurement in data["data_points"]:
                    measurement_time = datetime.datetime.fromisoformat(measurement["timestamp"])
                    send_time = datetime.datetime.fromisoformat(measurement["send_timestamp"])
                    measurement_latency = (received_time - measurement_time).total_seconds() * 1000  # Convert to milliseconds
                    send_latency = (received_time - send_time).total_seconds() * 1000  # Convert to milliseconds

                    # Calculate throughput from the latency between when the message from the device was sent to when it was received by the server
                    send_throughput = packet_size * 8 / (send_latency / 1000) # bps

                    # classify the connection based on latency and throughput
                    connection_classification = monitor.classify_connection(send_latency, send_throughput)

                    # Log the bulk upload
                    monitor.log_bulk_upload(measurement["device_id"], str(session_web_id), received_time, packet_size, measurement_time, measurement_latency, send_time, send_latency, send_throughput, connection_classification, measurement)


            await websocket.send("Message received by the server.")
    except websockets.ConnectionClosed:
        print("WebSocket connection closed.")

async def start_websocket_server():
    server = await websockets.serve(websocket_handler, "127.0.0.1", 8088)
    print("WebSocket server running on ws://127.0.0.1:8088")
    await server.wait_closed()

def run_monitoring_with_websocket():
    global monitor
    monitor = PassiveMonitoring(interface="lo", target_ip="127.0.0.1", target_port=8088)

    monitoring_thread = threading.Thread(target=monitor.start_monitoring)
    monitoring_thread.start()

    queue_thread = threading.Thread(target=monitor.process_queue)
    queue_thread.start()

    asyncio.run(start_websocket_server())

    # Stop the queue processing thread when the server stops
    monitor.queue.put(None)
    queue_thread.join()

if __name__ == "__main__":
    run_monitoring_with_websocket()