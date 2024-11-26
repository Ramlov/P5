import time
import requests
import json
import random
from scapy.all import sniff, TCP, IP
from time import sleep
from port_mapper import PortMatcher

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

with open(config['fd_profiles_file'], 'r') as file:
    fd_profiles = json.load(file)

NETWORK_PROFILES = config['network_profiles']
PACKET_LOSS = config['packet_loss']
port_sub = config['port_sub']
PORT_RANGE = range(config['port_range'][0], config['port_range'][1])
LAST_PROFILE = None
MATCHER = PortMatcher(PORT_RANGE)


def write_to_file(log):
    try:
        with open(config['log_file'], "a") as file:
            file.write(log)
        print(f"Logged: {log}") 
    except Exception as e:
        print(f"Error writing to file: {e}")

def sniff_packets():
    while True:
        sniff(prn=print_port, iface="br0")

def print_port(pkt):
    global LAST_PROFILE
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        
        chosen_port =  MATCHER.port_mapping(tcp_dport, tcp_sport)
        if chosen_port in PORT_RANGE:
            write_to_file(f"Source IP: {src_ip}, Destination IP: {dst_ip}, Source Port: {tcp_sport}, Destination Port: {tcp_dport}")
            
            device_id = get_id_from_port(chosen_port)
            if device_id < 0:
                write_to_file("No Device ID Found")
                return
                
            profile = fd_profiles[device_id]
            write_to_file(f"\n Network Profile for ID {device_id}: {profile}" )
            profile_type = profile.get("profile")
            if profile_type in NETWORK_PROFILES:
                if profile_type == LAST_PROFILE:
                    write_to_file(f"Profile {profile_type} already set")
                    return
                else:
                    packet_loss = PACKET_LOSS.get(profile_type, 0)
                    write_to_file(f"\n Packet loss for profile {profile_type}: {packet_loss}%")
                    delay_range = NETWORK_PROFILES[profile_type]
                    delay = random.randint(delay_range["min"], delay_range["max"])
                    write_to_file(f"\n Chosen delay for profile {profile_type}: {delay} ms")
                    packet_callback(delay, packet_loss)
                    LAST_PROFILE = profile_type
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
