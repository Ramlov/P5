# app.py

import json
import random
import requests
from flask import Flask, render_template, Response
from scapy.all import sniff, TCP, IP
from time import sleep

app = Flask(__name__)

# Load device profiles
with open('fd_profiles.json', 'r') as file:
    fd_profiles = json.load(file)

NETWORK_PROFILES = {
    "SLOW": {"min": 1000, "max": 2000},
    "NORMAL": {"min": 300, "max": 500},
    "GOOD": {"min": 50, "max": 300}
}

PORT_RANGE = range(3000, 3029)

def get_id_from_port(port):
    return port - 3000

def sniff_packets():
    """Generator function to sniff packets and yield data for streaming."""
    while True:
        sniff(prn=print_port, count=1, store=0)

def print_port(pkt):
    """Process a packet and yield information as a stream of text."""
    if IP in pkt and TCP in pkt:
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        
        # Only process packets within the specified port range
        if tcp_dport in PORT_RANGE:
            yield f"Source Port: {tcp_sport}, Destination Port: {tcp_dport}\n"
            
            device_id = get_id_from_port(tcp_dport)
            if device_id < 0 or device_id >= len(fd_profiles):
                yield "No Device ID Found\n"
                return
            
            profile = fd_profiles[device_id]
            yield f"Network Profile for ID {device_id}: {profile}\n"
            profile_type = profile.get("profile")
            if profile_type in NETWORK_PROFILES:
                packet_loss = {"GOOD": 2, "NORMAL": 5, "SLOW": 10}.get(profile_type, 0)
                yield f"Packet loss for profile {profile_type}: {packet_loss}%\n"
                delay_range = NETWORK_PROFILES[profile_type]
                delay = random.randint(delay_range["min"], delay_range["max"])
                yield f"Chosen delay for profile {profile_type}: {delay} ms\n"
                yield from packet_callback(delay, packet_loss)
            else:
                yield f"No network profile type found for {profile_type}\n"

def packet_callback(delay, packet_loss):
    """Send packet loss and delay data to the external API and yield the response."""
    payload_loss = {"percent": packet_loss}
    response_loss = requests.post(
        'http://192.168.1.8/api/disciplines/packet_loss',
        json=payload_loss
    )
    yield f"Response from packet loss API: {response_loss.text}\n"
    
    payload_delay = {'milliseconds': delay}
    response_delay = requests.post(
        'http://192.168.1.8/api/disciplines/packet_delay',
        json=payload_delay
    )
    yield f"Response from packet delay API: {response_delay.text}\n"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    """Flask endpoint to stream packet data to the client."""
    return Response(sniff_packets(), mimetype='text/plain')

if __name__ == "__main__":
    app.run(debug=True)
