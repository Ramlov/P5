import requests
import json
import random
from scapy.all import sniff, TCP

with open('fd_profiles.json', 'r') as file:
    fd_profiles = json.load(file)

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

packet_counter = 0

def sniff_packets():
    while True:
        sniff(prn=print_port, count=0)

def print_port(pkt):
    global packet_counter
    if TCP in pkt:
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        
        # Only process packets with destination ports within the range 3000-4000
        if 3000 <= tcp_dport <= 4000:
            print(f"Source Port: {tcp_sport}, Destination Port: {tcp_dport}")
            
            packet_counter += 1
            print(f"Total packets within port range 3000-4000: {packet_counter}")
            
            device_id = get_id_from_port(tcp_dport)
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
            #print("Packet outside port range 3000-4000, ignoring.")
    else:
        pass
        #print("Non-TCP packet received")

def packet_callback(delay):
    requests.post('http://localhost/api/disciplines/packet_delay', data=json.dumps({'milliseconds': delay}))

def get_id_from_port(port):
    if port > 3009:
        return port % 100
    elif port >= 3000:
        return port % 10
    else:
        return -1

if __name__ == "__main__":
    sniff_packets()