import requests
import json
from scapy import sniff, TCP
from scapy.all import *

def sniff_packets():
    while True:
        sniff(prn=print_port, count=1)

def print_port(pkt):
    if TCP in pkt:
        tcp_sport = pkt[TCP].sport
        tcp_dport = pkt[TCP].dport
        print(f"Source Port: {tcp_sport}, Destination Port: {tcp_dport}")
    else:
        print("Non-TCP packet received")

sniff_packets()

def packet_callback(delay):
    requests.post('http://localhost/api/disciplines/packet_delay', data=json.dumps({'milliseconds': delay}))