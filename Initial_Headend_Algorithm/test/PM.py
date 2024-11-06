# passive_monitoring.py

from scapy.all import sniff, IP, UDP, TCP
import time

class PassiveMonitoring:
    """Performs passive network monitoring using Scapy for packet capture and analysis."""

    def __init__(self, interface='lo', target_ip="127.0.0.1", target_port = 9090):
        """Initialize the passive monitoring instance."""
        self.interface = interface
        self.target_ip = target_ip
        self.target_port = target_port
        self.packet_count = 0
        self.udp_packet_count = 0
        self.tcp_packet_count = 0
        self.seen_packets = set()  # Initialize the set for deduplication

    def capture_packets(self):
        """Capture UDP and TCP packets continuously on the specified interface and process them.""" 

        filter_string = f"((udp or tcp) and dst host {self.target_ip} and dst port {self.target_port})"
        print(f"Starting packet capture on interface {self.interface} with filter: {filter_string}")
        # --- Complex filter strings ---

        # Capture only incoming packets to a specific IP and port:
        # filter_string = f"((udp or tcp) and dst host {self.target_ip} and dst port {self.target_port})"

        # Capture all TCP traffic on a specific port but only UDP packets from a specific IP:
        # filter_string = f"(tcp and port {self.target_port}) or (udp and src host {self.target_ip})"

        # Capture traffic from multiple IPs or ports:
        # filter_string = f"((udp or tcp) and (host {self.target_ip} or host {self.another_ip}) and (port {self.target_port} or port {self.another_port}))"

        sniff(iface=self.interface, filter=filter_string,prn=self.process_packet, store=0)

    def process_packet(self, packet):
        # """Route packet to appropriate handler based on protocol type."""
        if packet.haslayer(IP):
            if packet.haslayer(UDP):
                self.process_packet_udp(packet)
            elif packet.haslayer(TCP):
                self.process_packet_tcp(packet)
        

    def process_packet_udp(self, packet):
        """Process each UDP packet to extract and log details."""
        self.udp_packet_count += 1
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
        payload = bytes(packet[UDP].payload).decode(errors="ignore")  # Decode payload as a string

        print(f"Captured UDP packet from {src_ip}:{src_port} to {dst_ip}:{dst_port} with payload: {payload}")
        if self.udp_packet_count % 5 == 0:
            print(f"UDP packets captured so far: {self.udp_packet_count}")


    def process_packet_tcp(self, packet):
        """Process each TCP packet to extract and log details, including latency calculation if relevant."""
        self.tcp_packet_count += 1
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
        payload = bytes(packet[TCP].payload).decode(errors="ignore")  # Decode payload as a string

        print(f"Captured TCP packet from {src_ip}:{src_port} to {dst_ip}:{dst_port} with payload: {payload}")
        if self.tcp_packet_count % 5 == 0:
            print(f"TCP packets captured so far: {self.tcp_packet_count}")

    def start_monitoring(self):
        """Entry point for starting passive monitoring."""
        self.capture_packets()
