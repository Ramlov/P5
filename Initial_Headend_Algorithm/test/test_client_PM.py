# test_client.py

from scapy.all import IP, UDP, TCP, send
import time

def send_udp_packet(destination_ip, destination_port):
    packet = IP(dst=destination_ip) / UDP(dport=destination_port) / "Test UDP packet"
    send(packet)
    print(f"Sent UDP packet to {destination_ip}:{destination_port}")

def send_tcp_packet(destination_ip, destination_port):
    packet = IP(dst=destination_ip) / TCP(dport=destination_port, flags="S") / "Test TCP packet"
    send(packet)
    print(f"Sent TCP SYN packet to {destination_ip}:{destination_port}")

if __name__ == "__main__":
    destination_ip = "127.0.0.1"
    destination_port = 9090

    # Send UDP packets
    for i in range(5):
        send_udp_packet(destination_ip, destination_port)
        time.sleep(1)

    # Send TCP packets
    for i in range(5):
        send_tcp_packet(destination_ip, destination_port)
        time.sleep(1)
