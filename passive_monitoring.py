import asyncio
import websockets
import json
from scapy.all import sniff
from scapy.layers.inet import TCP
import ntplib
import threading
import time

class PassiveNetworkMonitor:
    def __init__(self, host='localhost', port=8765):
        """
        Initialize the Passive Network Monitoring Module.
        """
        self.host = host
        self.port = port
        self.ntp_offset = self.get_ntp_offset()
        print(f"NTP offset: {self.ntp_offset} seconds")
    
    def get_ntp_offset(self):
        """
        Get NTP offset to synchronize time with NTP server.
        """
        c = ntplib.NTPClient()
        response = c.request('pool.ntp.org')
        return response.offset

    async def start_server(self):
        """
        Start the WebSocket server to receive data from field devices.
        """
        server = await websockets.serve(self.process_upload, self.host, self.port)
        print(f"Server started on {self.host}:{self.port}")
        await asyncio.Future()  # Run forever

    async def process_upload(self, websocket, path):
        """
        Process incoming data uploads from field devices.
        """
        try:
            async for message in websocket:
                data = json.loads(message)
                device_id = data['device_id']
                send_timestamp = float(data['send_timestamp']) + self.ntp_offset
                print(f"Received upload from Device ID: {device_id}")
                # Start packet capture
                packets = []
                stop_sniff_event = threading.Event()
                sniff_thread = threading.Thread(target=self.capture_packets, args=(packets, stop_sniff_event))
                sniff_thread.start()
                # Simulate processing time (assuming data is being received)
                await asyncio.sleep(0.1)  # Adjust as necessary
                # Processing is done, stop packet capture
                stop_sniff_event.set()
                sniff_thread.join()
                # Calculate metrics
                metrics = self.calculate_metrics(packets, send_timestamp)
                # Classify connection
                classification = self.classify_connection(metrics['average_latency'], metrics['throughput'])
                # Print summary
                self.print_summary(device_id, metrics, classification)
        except websockets.exceptions.ConnectionClosed:
            pass

    def capture_packets(self, packets, stop_event):
        """
        Capture TCP packets using Scapy.
        """
        def packet_handler(pkt):
            if pkt.haslayer(TCP) and pkt[TCP].dport == self.port:
                packets.append(pkt)
        def stop_filter(pkt):
            return stop_event.is_set()
        sniff(filter=f"tcp port {self.port}", prn=packet_handler, stop_filter=stop_filter)

    def calculate_metrics(self, packets, send_timestamp):
        """
        Calculate metrics based on captured packets.
        """
        packet_count = len(packets)
        if packet_count == 0:
            return {
                'packet_count': 0,
                'total_data_size': 0,
                'total_time': 0,
                'average_latency': 0,
                'throughput': 0
            }
        arrival_times = [pkt.time for pkt in packets]
        packet_sizes = [len(pkt) for pkt in packets]
        total_data_size = sum(packet_sizes)
        total_time = max(arrival_times) - min(arrival_times)
        average_latency = ((sum(arrival_times) / packet_count) - send_timestamp) * 1000  # in ms
        throughput = (total_data_size * 8) / (total_time * 1000)  # in kbps
        return {
            'packet_count': packet_count,
            'total_data_size': total_data_size,
            'total_time': total_time,
            'average_latency': average_latency,
            'throughput': throughput
        }

    def classify_connection(self, average_latency, throughput):
        """
        Classify the connection quality based on average latency and throughput.
        """
        # Classify latency
        if average_latency < 100:
            latency_class = 'Excellent'
        elif average_latency < 300:
            latency_class = 'Good'
        else:
            latency_class = 'Poor'
        # Classify throughput
        if throughput > 500:
            throughput_class = 'Excellent'
        elif throughput > 200:
            throughput_class = 'Good'
        else:
            throughput_class = 'Poor'
        # Overall classification
        if latency_class == 'Poor' or throughput_class == 'Poor':
            overall_class = 'Poor'
        elif latency_class == 'Good' or throughput_class == 'Good':
            overall_class = 'Good'
        else:
            overall_class = 'Excellent'
        return overall_class

    def print_summary(self, device_id, metrics, classification):
        """
        Print the metrics and connection classification.
        """
        print(f"Device ID: {device_id}")
        print(f"Packet Count: {metrics['packet_count']}")
        print(f"Total Data Size: {metrics['total_data_size']} bytes")
        print(f"Total Time: {metrics['total_time']} seconds")
        print(f"Average Latency per Packet: {metrics['average_latency']} ms")
        print(f"Throughput: {metrics['throughput']} kbps")
        print(f"Connection Classification: {classification}")
        print("---------------------------------------------------")

    def run(self):
        """
        Run the Passive Network Monitoring Module.
        """
        asyncio.run(self.start_server())
