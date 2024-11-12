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

PACKET_LOSS_SEQUENCES = {
    0: {"index": -1, "sequence": [0, 0, 0, 0, 0, 1, 0, 1, 0]},
    1: {"index": -1, "sequence": [0, 1, 0, 1, 0, 1, 0, 0, 0]},
    2: {"index": -1, "sequence": [0, 1]}
}

PORT_RANGE = range(3000, 3029)

def sniff_packets():
    while True:
        sniff(prn=print_port, count=1)

def print_port(pkt):
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        
        # Only process packets with destination ports within the range 3000-4000
        if tcp_dport in PORT_RANGE:
            print(f"Source Port: {tcp_sport}, Destination Port: {tcp_dport}")

            device_id = get_id_from_port(tcp_dport)
            if device_id < 0:
                print("No Device ID Found")
                return

            # Check for packet loss
            index = PACKET_LOSS_SEQUENCES[device_id]["index"]
            print(f"Packet loss Sequence Index: {index}")
            seq = PACKET_LOSS_SEQUENCES[device_id]["sequence"]
            print(f"Current Sequence Index: {seq[index]}")

            PACKET_LOSS_SEQUENCES[device_id]["index"] = PACKET_LOSS_SEQUENCES[device_id]["index"] + 1

            if PACKET_LOSS_SEQUENCES[device_id]["index"] > len(seq):
                print("Reset Sequence")
                PACKET_LOSS_SEQUENCES[device_id]["index"] = -1

            if seq[index] == 1:
                print(f"Packet Loss!!")
                packet_callback(1, True, src_ip, tcp_sport)
                return

            
        
            

            profile = fd_profiles[device_id]
            print(f"Network Profile for ID {device_id}: {profile}")
            profile_type = profile.get("profile")
            if profile_type in NETWORK_PROFILES:
                delay_range = NETWORK_PROFILES[profile_type]
                delay = random.randint(delay_range["min"], delay_range["max"])
                print(f"Chosen delay for profile {profile_type}: {delay} ms")
                packet_callback(delay)
            else:
                print(f"No network profile type found for {profile_type}")

def packet_callback(delay, packet_loss=False, ip=None, port=None):
    if packet_loss:
        payload_loss = [
            {
                "ip": str(ip),
                "port": port,
                "destination_ip": "127.0.0.1",
                "destination_port": 10,
                "protocol": "tcp"
            }
        ]
        response_loss = requests.post(
            'http://192.168.1.8/api/ipredirect',
            json=payload_loss
        )
        print(f"Response from redirect: {response_loss.text}")

        # sleep(2)
        # payload_remove_loss = [
        #     {
        #         "remove_ip_redirect": "1",
        #         "ip": str(ip),
        #         "port": port,
        #         "destination_ip": "127.0.0.1",
        #         "destination_port": 10,
        #         "protocol": "tcp"
        #     }
        # ]
        # response_clear = requests.post(
        #     'http://192.168.1.8/api/ipredirect', json=payload_remove_loss
        # )
        # print(f"Response from clear: {response_clear.text}")
        return
    payload = {'milliseconds': delay}
    requests.post(
        'http://192.168.1.8/api/disciplines/packet_delay',
        json=payload
    )



def get_id_from_port(port):
    if port > 3009:
        return port % 100
    elif port >= 3000:
        return port % 10
    else:
        return -1

if __name__ == "__main__":
    sniff_packets()