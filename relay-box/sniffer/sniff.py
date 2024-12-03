import time
import requests
import json
import random
from scapy.all import sniff, TCP, IP
from time import sleep
from port_mapper import PortMatcher

# Load configurations
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

with open(config['fd_profiles_file'], 'r') as file:
    fd_profiles = json.load(file)

NETWORK_PROFILES = config['network_profiles']
PACKET_LOSS = config['packet_loss']
THROUGHPUT = config.get('throughput', {})  # Load throughput if available
port_sub = config['port_sub']
port_sub_bulk = config['port_sub_bulk']
burst_bytes = config.get('burst_bytes', 1024)
PORT_RANGE = range(config['port_range'][0], config['port_range'][1])
LAST_PROFILE = None
MATCHER = PortMatcher(PORT_RANGE)
ignore_ports = [80, 443, 22, 5005]

# Utility to write logs to file
def write_to_file(log):
    try:
        with open(config['log_file'], "a") as file:
            file.write(log)
    except Exception as e:
        print(f"Error writing to file: {e}")

# Packet sniffing logic
def sniff_packets():
    while True:
        sniff(prn=print_port, iface="br0")

# Processing each packet
def print_port(pkt):
    global LAST_PROFILE
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport

        chosen_port = min(tcp_dport, tcp_sport)
        if chosen_port not in ignore_ports:
            print(f"Source IP (before chosen port): {src_ip}, Destination IP: {dst_ip}, Source Port: {tcp_sport}, Destination Port: {tcp_dport}")
            print(f"Chosen Port: {chosen_port}")
            if chosen_port in PORT_RANGE:
                write_to_file(f"Source IP: {src_ip}, Destination IP: {dst_ip}, Source Port: {tcp_sport}, Destination Port: {tcp_dport}")
                
                device_id = get_id_from_port(chosen_port)
                print(f"Device ID: {device_id}")
                if device_id < 0:
                    write_to_file("No Device ID Found")
                    return
                    
                profile = fd_profiles[device_id]
                write_to_file(f"\n Network Profile for ID {device_id}: {profile}" )
                profile_type = profile.get("profile")
                if profile_type in NETWORK_PROFILES:
                    if profile_type == LAST_PROFILE:
                        write_to_file(f"\n Profile {profile_type} already set")
                        return
                    else:
                        packet_loss = PACKET_LOSS.get(profile_type, 0)
                        write_to_file(f"\n Packet loss for profile {profile_type}: {packet_loss}%")
                        delay_range = NETWORK_PROFILES[profile_type]
                        delay = random.randint(delay_range["min"], delay_range["max"])
                        write_to_file(f"\n Chosen delay for profile {profile_type}: {delay} ms")
                        
                        # Adding throughput handling
                        throughput_range = THROUGHPUT.get(profile_type, {"min": 0, "max": 0})
                        throughput = random.randint(throughput_range["min"], throughput_range["max"])
                        write_to_file(f"\n Chosen throughput for profile {profile_type}: {throughput} Mbps")
                        
                        packet_callback(delay, packet_loss, throughput)
                        LAST_PROFILE = profile_type
                else:
                    write_to_file(f"\n No network profile type found for {profile_type}")

# Callback for packet simulation
def packet_callback(delay, packet_loss, throughput):
    payload_loss = {"percent": packet_loss}
    try:
        response_loss = requests.post(
            config['api_endpoints']['packet_loss'],
            json=payload_loss
        )
        write_to_file(f"Response from packet_loss: {response_loss.text}")
    except Exception as e:
        write_to_file(f"Error in packet_loss request: {e}")

    payload_delay = {'milliseconds': delay}
    try:
        response_delay = requests.post(
            config['api_endpoints']['packet_delay'],
            json=payload_delay
        )
        write_to_file(f"Response from packet_delay: {response_delay.text}" + "\n")
    except Exception as e:
        write_to_file(f"Error in packet_delay request: {e}" + "\n")
        
    payload_rate_control = {
        "kbit": throughput * 1000,  # Converting Mbps to kbps
        "latency_milliseconds": 1000,
        "burst_bytes": burst_bytes
    }
    try:
        response_rate_control = requests.post(
            config['api_endpoints']['packet_rate_control'],
            json=payload_rate_control
        )
        write_to_file(f"Response from packet_rate_control: {response_rate_control.text}" + "\n")
    except Exception as e:
        write_to_file(f"Error in packet_rate_control request: {e}" + "\n")


# Helper to map port to device ID
def get_id_from_port(port):
    if port >= port_sub_bulk:
        print(port, port_sub_bulk), "BULK"
        return port - port_sub_bulk
    else:
        print(port, port_sub, "NOT BULK")
        return port - port_sub

# Main execution
if __name__ == "__main__":
    sniff_packets()
