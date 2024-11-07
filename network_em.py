import os
import json
import random
import time
import logging
from scapy.all import sniff, sendp, Ether, IP, TCP, UDP

# Set up logging
logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Define network profile settings
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

# Network Emulator Class
class NetworkEmulator:
    def __init__(self, profile="NORMAL"):
        self.profile = NETWORK_PROFILES.get(profile, NETWORK_PROFILES["NORMAL"])

    def get_latency(self):
        return random.uniform(self.profile["min"], self.profile["max"]) / 1000  # convert ms to seconds

    def should_drop_packet(self, fd_id):
        sequence_info = PACKET_LOSS_SEQUENCES.get(fd_id)
        if sequence_info:
            index = sequence_info["index"]
            drop = sequence_info["sequence"][index] == 1
            # Update index for next packet
            sequence_info["index"] = (index + 1) % len(sequence_info["sequence"])
            return drop
        return False  # Default to no packet loss if no sequence found

    def apply_profile(self, fd_id):
        if self.should_drop_packet(fd_id):
            logging.info("Packet dropped due to packet loss sequence.")
            return False
        latency = self.get_latency()
        logging.info(f"Applying latency of {latency * 1000:.2f} ms")
        time.sleep(latency)
        return True

# Packet Relay Function
def relay_packet(packet):
    fd_id = 2  # Field device ID (for demo purposes; change as needed)
    
    # Identify source and destination ports if present
    src_port = dst_port = None
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
    else:
        src_ip = dst_ip = "N/A"
    
    # Log packet information
    logging.info(f"Received packet on {interface_in} - Source IP: {src_ip}, Source Port: {src_port}, "
                 f"Destination IP: {dst_ip}, Destination Port: {dst_port}")
    
    # Apply network emulation profile
    if network_emulator.apply_profile(fd_id):
        sendp(packet, iface=interface_out, verbose=False)
        logging.info(f"Packet relayed to output interface {interface_out}.")
    else:
        logging.info("Packet was dropped.")

# Main Capture and Relay Loop
def start_bridge():
    logging.info(f"Starting packet bridge: {interface_in} -> {interface_out}")
    sniff(iface=interface_in, prn=relay_packet, store=0)

# Load Configuration
def load_configuration():
    global interface_in, interface_out, network_emulator
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, "config.json")
    
    with open(config_file_path, "r") as file:
        config = json.load(file)
        interface_in = config.get("NetworkInterfaces", ["eth0", "eth1"])[0]
        interface_out = config.get("NetworkInterfaces", ["eth0", "eth1"])[1]
        profile = config.get("NetworkProfile", "NORMAL")
        network_emulator = NetworkEmulator(profile=profile)
        logging.info(f"Loaded configuration: {config}")

if __name__ == "__main__":
    load_configuration()
    start_bridge()
