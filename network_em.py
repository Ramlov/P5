import os
import json
import random
import time
import logging
import threading
from scapy.all import sniff, sendp, Ether, IP, TCP, UDP

# Set up logging
logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Define general network profiles
NETWORK_PROFILES = {
    "SLOW": {"min": 1000, "max": 2000},
    "NORMAL": {"min": 300, "max": 500},
    "GOOD": {"min": 50, "max": 300}
}

PACKET_LOSS_SEQUENCES = {
    0: {"index": 0, "sequence": [0, 0, 1, 0, 0, 1, 0, 1, 0]},
    1: {"index": 0, "sequence": [0, 1, 0, 1, 0, 1, 0, 0, 0]},
    2: {"index": 0, "sequence": [0, 1]}
}

FD_PROFILES = {}  # Loaded from fd_profiles.json

# Helper function to log and print messages
def log_and_print(message):
    logging.info(message)
    print(message)

# Network Emulator Class
class NetworkEmulator:
    def __init__(self, profile="NORMAL"):
        self.profile = NETWORK_PROFILES.get(profile, NETWORK_PROFILES["NORMAL"])

    def get_latency(self):
        return random.uniform(self.profile["min"], self.profile["max"]) / 1000  # Convert ms to seconds

    def should_drop_packet(self, fd_id):
        sequence_info = PACKET_LOSS_SEQUENCES.get(fd_id)
        if sequence_info:
            index = sequence_info["index"]
            drop = sequence_info["sequence"][index] == 1
            sequence_info["index"] = (index + 1) % len(sequence_info["sequence"])
            return drop
        return False

    def apply_profile(self, fd_id):
        if self.should_drop_packet(fd_id):
            log_and_print(f"Packet dropped due to packet loss sequence for FD ID {fd_id}.")
            return False
        latency = self.get_latency()
        log_and_print(f"Applying latency of {latency * 1000:.2f} ms for FD ID {fd_id}")
        time.sleep(latency)
        return True

# Packet Handler
def handle_packet(packet):
    src_ip = dst_ip = src_port = dst_port = "0"
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport

    fd_id = get_id_from_port(src_port)  # Determine FD ID from source port
    profile = FD_PROFILES.get(fd_id, "NORMAL")  # Get profile for FD ID, default to NORMAL
    network_emulator = NetworkEmulator(profile=profile)  # Create emulator instance for FD

    log_and_print(f"Received packet on {interface_in} - Source IP: {src_ip}, Source Port: {src_port}, "
                  f"Destination IP: {dst_ip}, Destination Port: {dst_port}, Field device id: {fd_id}, Profile: {profile}")

    # Apply profile-specific modifications
    if network_emulator.apply_profile(fd_id):
        sendp(packet, iface=interface_out, verbose=False)
        log_and_print(f"Packet relayed to output interface {interface_out}.")
    else:
        log_and_print("Packet was dropped.")
    
    # Log total number of active threads
    log_and_print(f"Total active threads: {threading.active_count() - 1}")  # Subtract 1 for the main thread

# Packet Relay Function (spawns threads for each packet)
def relay_packet(packet):
    src_ip = dst_ip = "Unknown"
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst

    # Log and print the interface, packet size, and IP addresses
    log_and_print(f"Received packet on {interface_in} - Size: {len(packet)} bytes, Source IP: {src_ip}, Destination IP: {dst_ip}")

    if len(packet) > 1500:
        log_and_print("Packet ignored: size exceeds 1500 bytes.")
        sendp(packet, iface=interface_out, verbose=False)
        return

    # Filter packets based on source and destination ports (3000-4000 range)
    src_port = dst_port = 0
    if IP in packet:
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport

    # Check if both ports are within the specified range
    if not (3000 <= src_port <= 4000) or not (3000 <= dst_port <= 4000):
        # Relay packet directly to output interface without processing
        sendp(packet, iface=interface_out, verbose=False)
        log_and_print("Packet relayed directly (outside 3000-4000 port range).")
        return

    # Spawn a new thread for each packet that is within range
    packet_thread = threading.Thread(target=handle_packet, args=(packet,))
    packet_thread.start()


# Main Capture and Relay Loop
def start_bridge():
    log_and_print(f"Starting packet bridge: {interface_in} -> {interface_out}")
    sniff(iface=interface_in, prn=relay_packet, store=0)

# Map FD ID based on port
def get_id_from_port(port):
    if port > 3009:
        return port % 100
    elif port >= 3000:
        return port % 10
    else:
        return 0

# Load Configuration
def load_configuration():
    global interface_in, interface_out, FD_PROFILES
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load network configuration
    config_file_path = os.path.join(script_dir, "config.json")
    with open(config_file_path, "r") as file:
        config = json.load(file)
        interface_in = config.get("NetworkInterfaces", ["eth0", "eth1"])[0]
        interface_out = config.get("NetworkInterfaces", ["eth0", "eth1"])[1]
        log_and_print(f"Loaded network configuration: {config}")
    
    # Load field device profiles
    fd_profiles_path = os.path.join(script_dir, "fd_profiles.json")
    with open(fd_profiles_path, "r") as file:
        fd_profiles = json.load(file)
        FD_PROFILES = {item["id"]: item["profile"] for item in fd_profiles}
        log_and_print(f"Loaded field device profiles: {FD_PROFILES}")

if __name__ == "__main__":
    load_configuration()
    start_bridge()
