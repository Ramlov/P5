import time
import requests
import json
import random
from scapy.all import sniff, TCP, IP
from time import sleep
from port_mapper import PortMatcher

# Load configurations from external files
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

with open(config['fd_profiles_file'], 'r') as file:
    fd_profiles = json.load(file)

# Constants and configurations
NETWORK_PROFILES = config['network_profiles']
PACKET_LOSS = config['packet_loss']
THROUGHPUT = config.get('throughput', {})  # Optional throughput configuration
PORT_RANGE = range(config['port_range'][0], config['port_range'][1])
ignore_ports = [80, 443, 22, 5005]  # Common ports to ignore

# Port-specific configurations
port_sub = config['port_sub']
port_sub_bulk = config['port_sub_bulk']
burst_bytes = config('burst_bytes', 1024)
delay_rate_control = config['delay_rate_control']

# Variables
LAST_PROFILE = None
MATCHER = PortMatcher(PORT_RANGE)

# Utility: Write logs to a file
def write_to_file(log):
    """Append a log entry to the configured log file."""
    try:
        with open(config['log_file'], "a") as file:
            file.write(f"{log}\n")
    except Exception as e:
        print(f"Error writing to file: {e}")

# Packet sniffing main function
def sniff_packets():
    """Start sniffing packets on the specified network interface."""
    while True:
        sniff(prn=process_packet, iface="br0")

# Packet processing logic
def process_packet(pkt):
    """Process each packet and determine actions based on its attributes."""
    global LAST_PROFILE

    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport

        chosen_port = min(tcp_sport, tcp_dport)
        if chosen_port not in ignore_ports:
            write_to_file(f"--- Packet Details ---\n"
                          f"Source IP: {src_ip}\n"
                          f"Destination IP: {dst_ip}\n"
                          f"Source Port: {tcp_sport}\n"
                          f"Destination Port: {tcp_dport}\n"
                          f"Chosen Port: {chosen_port}")

            if chosen_port in PORT_RANGE:
                process_network_profile(chosen_port, src_ip, dst_ip, tcp_sport, tcp_dport)

# Network profile processing
def process_network_profile(port, src_ip, dst_ip, src_port, dst_port):
    """Handle logic related to network profiles based on the port."""
    global LAST_PROFILE

    device_id = get_id_from_port(port)
    if device_id < 0:
        write_to_file("No Device ID Found")
        return

    profile = fd_profiles.get(device_id)
    if not profile:
        write_to_file(f"No profile found for device ID {device_id}")
        return

    write_to_file(f"Device ID: {device_id}\nNetwork Profile: {profile}")
    profile_type = profile.get("profile")

    if profile_type in NETWORK_PROFILES:
        if profile_type == LAST_PROFILE:
            write_to_file(f"Profile {profile_type} already active.")
            return

        # Fetch packet loss, delay, and throughput for the profile
        packet_loss = PACKET_LOSS.get(profile_type, 0)
        delay_range = NETWORK_PROFILES[profile_type]
        delay = random.randint(delay_range["min"], delay_range["max"])
        throughput_range = THROUGHPUT.get(profile_type, {"min": 0, "max": 0})
        throughput = random.randint(throughput_range["min"], throughput_range["max"])

        write_to_file(f"Packet Loss: {packet_loss}%\n"
                      f"Delay: {delay} ms\n"
                      f"Throughput: {throughput} Mbps")

        # Apply the network profile settings
        apply_network_profile(delay, packet_loss, throughput)
        LAST_PROFILE = profile_type
    else:
        write_to_file(f"No network profile type found for {profile_type}")

# Apply network profile settings
def apply_network_profile(delay, packet_loss, throughput):
    """Send API requests to apply packet delay, loss, and throughput."""
    try:
        # Packet loss
        payload_loss = {"percent": packet_loss}
        response_loss = requests.post(config['api_endpoints']['packet_loss'], json=payload_loss)
        write_to_file(f"Packet Loss API Response: {response_loss.text}")

        # Packet delay
        payload_delay = {'milliseconds': delay}
        response_delay = requests.post(config['api_endpoints']['packet_delay'], json=payload_delay)
        write_to_file(f"Packet Delay API Response: {response_delay.text}")

        # Rate control
        payload_rate_control = {
            "kbit": throughput * 1000,  # Mbps to Kbps
            "latency_milliseconds": delay_rate_control,
            "burst_bytes": burst_bytes
        }
        response_rate_control = requests.post(config['api_endpoints']['packet_rate_control'], json=payload_rate_control)
        write_to_file(f"Rate Control API Response: {response_rate_control.text}")
        write_to_file(f"*************************************************************")
    except Exception as e:
        write_to_file(f"Error applying network profile: {e}")

# Helper: Map port to device ID
def get_id_from_port(port):
    """Convert a port number to a device ID."""
    if port >= port_sub_bulk:
        return port - port_sub_bulk
    return port - port_sub

# Main execution point
if __name__ == "__main__":
    sniff_packets()
