import socket
import os

# Define the two interfaces to monitor
INTERFACE_INBOUND = "eth0"
INTERFACE_OUTBOUND = "eth1"

def create_socket(interface):
    """
    Creates a raw socket for the specified interface.
    """
    raw_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    raw_sock.bind((interface, 0))
    return raw_sock

def relay_packets(sock_in, sock_out, buffer_size=65535):
    """
    Continuously reads packets from the input socket and forwards them to the output socket.
    """
    while True:
        # Receive a packet from the input socket
        packet, _ = sock_in.recvfrom(buffer_size)
        
        # Extract IP information for logging
        src_ip, dst_ip = packet[26:30], packet[30:34]  # Extract IP addresses from packet (for IPv4)
        src_ip = '.'.join(map(str, src_ip))
        dst_ip = '.'.join(map(str, dst_ip))
        print(f"Relaying Packet - Src IP: {src_ip}, Dst IP: {dst_ip}")

        # Send the packet out via the output socket
        sock_out.send(packet)

# Set up raw sockets for both interfaces
sock_inbound = create_socket(INTERFACE_INBOUND)
sock_outbound = create_socket(INTERFACE_OUTBOUND)

try:
    print(f"Starting packet relay between {INTERFACE_INBOUND} and {INTERFACE_OUTBOUND}...")
    # Run relay from inbound to outbound and vice versa
    while True:
        # Relay packets from eth0 to eth1 and vice versa
        relay_packets(sock_inbound, sock_outbound)
        relay_packets(sock_outbound, sock_inbound)
except KeyboardInterrupt:
    print("Stopping packet relay.")
finally:
    sock_inbound.close()
    sock_outbound.close()
