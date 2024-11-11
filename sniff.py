import socket
import struct
import json
import random
from time import sleep

# Load the JSON data from the file
with open('fd_profiles.json', 'r') as file:
    fd_profiles = json.load(file)

NETWORK_PROFILES = {
    "SLOW": {"min": 1000, "max": 2000},
    "NORMAL": {"min": 300, "max": 500},
    "GOOD": {"min": 50, "max": 300}
}

packet_counter = 0
whitelist_ips = {"192.168.1.7"}  # Add the IPs you want to whitelist

def get_id_from_port(port):
    if port > 3009:
        return port % 100
    elif port >= 3000:
        return port % 10
    else:
        return -1

def packet_callback(delay):
    # Implement the delay handling as needed
    pass

def parse_packet(packet):
    global packet_counter
    # Unpack Ethernet frame
    eth_length = 14
    eth_header = packet[:eth_length]

    # Get IP protocol
    ip_header = packet[eth_length:eth_length+20]
    iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
    version_ihl = iph[0]
    version = version_ihl >> 4

    if version == 4:
        iph_length = (version_ihl & 0xF) * 4
        protocol = iph[6]
        src_ip = socket.inet_ntoa(iph[8])
        dst_ip = socket.inet_ntoa(iph[9])

        # Skip packets from whitelisted IPs
        # if src_ip in whitelist_ips or dst_ip in whitelist_ips:
            # return

        # TCP protocol
        if protocol == 6:
            t = eth_length + iph_length
            tcp_header = packet[t:t+20]
            tcph = struct.unpack('!HHLLBBHHH', tcp_header)

            tcp_sport = tcph[0]
            tcp_dport = tcph[1]
            tcp_seq = tcph[2]

            # Only process packets with destination ports within the range 3000-4000
            if 3000 <= tcp_dport <= 4000:
                print(f"Source Port: {tcp_sport}, Destination Port: {tcp_dport}, Sequence Number: {tcp_seq}, src_ip: {src_ip}, dst_ip: {dst_ip}")

                packet_counter += 1
                print(f"Total packets within port range 3000-4000: {packet_counter}")

                device_id = str(get_id_from_port(tcp_dport))
                if device_id in fd_profiles:
                    profile = fd_profiles[device_id]
                    print(f"Network Profile for ID {device_id}: {profile}")
                    profile_type = profile.get("profile_type")
                    if profile_type in NETWORK_PROFILES:
                        delay_range = NETWORK_PROFILES[profile_type]
                        delay = random.randint(delay_range["min"], delay_range["max"])
                        print(f"Chosen delay for profile {profile_type}: {delay} ms")
                        packet_callback(delay)
                    else:
                        print(f"No network profile type found for {profile_type}")
                else:
                    print(f"No network profile found for ID {device_id}")
            else:
                pass
                # Packet outside port range 3000-4000, ignoring.
        else:
            pass
            # Non-TCP packet received
    else:
        pass
        # Non-IPv4 packet received

    # Add a delay of 10 milliseconds before processing the next packet
    sleep(0.01)

def sniff_packets():
    try:
        # Create a raw socket and bind it to the interface
        conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
        conn.bind(('br0', 0))  # Replace 'br0' with your interface

        while True:
            raw_data, addr = conn.recvfrom(65535)
            parse_packet(raw_data)
    except PermissionError:
        print("Permission denied: You might need to run this script with elevated privileges.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    sniff_packets()