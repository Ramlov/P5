import requests
import json
import random
from scapy.all import sniff, TCP, IP
from time import sleep

with open('fd_profiles.json', 'r') as file:
    fd_profiles = json.load(file)

NETWORK_PROFILES = {
    "SLOW": {"min": 1000, "max": 2000},
    "NORMAL": {"min": 300, "max": 500},
    "GOOD": {"min": 50, "max": 300}
}

PORT_RANGE = range(3000, 3029)

def write_to_file(log):
    try:
        with open("log.txt", "a") as file:
            file.write(log + "\n")
        print(f"Logged: {log}")  # Debugging print statement
    except Exception as e:
        print(f"Error writing to file: {e}")

def sniff_packets():
    while True:
        sniff(prn=print_port, count=1)

def print_port(pkt):
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        
        # Only process packets with destination ports within the range 3000-3029
        if tcp_dport in PORT_RANGE:
            write_to_file(f"Source IP: {src_ip}, Destination IP: {dst_ip}, Source Port: {tcp_sport}, Destination Port: {tcp_dport}")

            device_id = get_id_from_port(tcp_dport)
            if device_id < 0:
                write_to_file("No Device ID Found")
                return
                
            profile = fd_profiles[device_id]
            write_to_file(f"Network Profile for ID {device_id}: {profile}")
            profile_type = profile.get("profile")
            if profile_type in NETWORK_PROFILES:
                packet_loss = {"GOOD": 2, "NORMAL": 5, "SLOW": 10}.get(profile_type, 0)
                write_to_file(f"Packet loss for profile {profile_type}: {packet_loss}%")
                delay_range = NETWORK_PROFILES[profile_type]
                delay = random.randint(delay_range["min"], delay_range["max"])
                write_to_file(f"Chosen delay for profile {profile_type}: {delay} ms")
                packet_callback(delay, packet_loss)
            else:
                write_to_file(f"No network profile type found for {profile_type}")

def packet_callback(delay, packet_loss):
    payload_loss = {"percent": packet_loss}
    try:
        # response_loss = requests.post(
        #     'http://192.168.1.8/api/disciplines/packet_loss',
        #     json=payload_loss
        # )
        # write_to_file(f"Response from packet_loss: {response_loss.text}")
        pass
    except Exception as e:
        write_to_file(f"Error in packet_loss request: {e}")

    payload = {'milliseconds': delay}
    try:
        # response_delay = requests.post(
        #     'http://192.168.1.8/api/disciplines/packet_delay',
        #     json=payload
        # )
        # write_to_file(f"Response from packet_delay: {response_delay.text}")
        pass
    except Exception as e:
        write_to_file(f"Error in packet_delay request: {e}")

def get_id_from_port(port):
    return port - 3000

if __name__ == "__main__":
    sniff_packets()