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

def sniff_packets():
    while True:
        yield from sniff(lambda: (yield from print_port()), count=1)

def print_port(pkt):
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        
        # Only process packets with destination ports within the range 3000-4000
        if tcp_dport in PORT_RANGE:
            yield(f"Source Port: {tcp_sport}, Destination Port: {tcp_dport}")

            device_id = get_id_from_port(tcp_dport)
            if device_id < 0:
                yield("No Device ID Found")
                return
                
            profile = fd_profiles[device_id]
            yield(f"Network Profile for ID {device_id}: {profile}")
            profile_type = profile.get("profile")
            if profile_type in NETWORK_PROFILES:
                packet_loss = {"GOOD": 2, "NORMAL": 5, "SLOW": 10}.get(profile_type, 0)
                yield(f"Packet loss for profile {profile_type}: {packet_loss}%")
                delay_range = NETWORK_PROFILES[profile_type]
                delay = random.randint(delay_range["min"], delay_range["max"])
                yield(f"Chosen delay for profile {profile_type}: {delay} ms")
                yield from packet_callback(delay, packet_loss)
            else:
                yield(f"No network profile type found for {profile_type}")

def packet_callback(delay, packet_loss):
    payload_loss = {
                    "percent": packet_loss
                    }
    response_loss = requests.post(
        'http://192.168.1.8/api/disciplines/packet_loss',
        json=payload_loss
    )
    yield(f"Response from redirect: {response_loss.text}")
    payload = {'milliseconds': delay}
    requests.post(
        'http://192.168.1.8/api/disciplines/packet_delay',
        json=payload
    )

def get_id_from_port(port):
    return port - 3000

if __name__ == "__main__":
    sniff_packets()