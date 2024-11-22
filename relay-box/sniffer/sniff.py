import requests
import json
import random
from scapy.all import sniff, TCP, IP
from time import sleep

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

with open(config['fd_profiles_file'], 'r') as file:
    fd_profiles = json.load(file)

NETWORK_PROFILES = config['network_profiles']
port_sub = config['port_sub']
PORT_RANGE = range(config['port_range'][0], config['port_range'][1])

def write_to_file(log):
    try:
        with open(config['log_file'], "a") as file:
            file.write(log)
        # print(f"Logged: {log}") 
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
        
        if tcp_dport in PORT_RANGE:
            write_to_file(f"Source IP: {src_ip}, Destination IP: {dst_ip}, Source Port: {tcp_sport}, Destination Port: {tcp_dport}")

            device_id = get_id_from_port(tcp_dport)
            if device_id < 0:
                write_to_file("No Device ID Found")
                return
                
            profile = fd_profiles[device_id]
            write_to_file(f"\n Network Profile for ID {device_id}: {profile}" )
            profile_type = profile.get("profile")
            if profile_type in NETWORK_PROFILES:
                packet_loss = {"GOOD": 2, "NORMAL": 5, "SLOW": 10}.get(profile_type, 0)
                write_to_file(f"\n Packet loss for profile {profile_type}: {packet_loss}%")
                delay_range = NETWORK_PROFILES[profile_type]
                delay = random.randint(delay_range["min"], delay_range["max"])
                write_to_file(f"\n Chosen delay for profile {profile_type}: {delay} ms")
                packet_callback(delay, packet_loss)
            else:
                write_to_file(f"No network profile type found for {profile_type}")

def packet_callback(delay, packet_loss):
    payload_loss = {"percent": packet_loss}
    try:
        response_loss = requests.post(
            config['api_endpoints']['packet_loss'],
            json=payload_loss
        )
        write_to_file(f"Response from packet_loss: {response_loss.text}")
    except Exception as e:
        write_to_file(f"Error in packet_loss request: {e}")

    payload = {'milliseconds': delay}
    try:
        response_delay = requests.post(
            config['api_endpoints']['packet_delay'],
            json=payload
        )
        write_to_file(f"Response from packet_delay: {response_delay.text}" + "\n")
    except Exception as e:
        write_to_file(f"Error in packet_delay request: {e}" + "\n")

def get_id_from_port(port):
    return port - port_sub

if __name__ == "__main__":
    sniff_packets()