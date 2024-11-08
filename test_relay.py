# Disable route autoloading before importing Scapy
from scapy.config import conf
conf.route_autoload = False
conf.route6_autoload = False

# Import Scapy modules
from scapy.all import sniff, sendp, Ether, IP, TCP, UDP
from scapy.layers.inet import ICMP

# Define the two interfaces to monitor
INTERFACE_INBOUND = "eth0"
INTERFACE_OUTBOUND = "eth1"

# Limit the layers to Ether, IP, TCP, UDP, and ICMP to speed up processing
conf.layers.filter([Ether, IP, TCP, UDP, ICMP])

# Define a BPF filter for IP, TCP, and UDP packets only
BPF_FILTER = "ip or tcp or udp"

def print_packet_info(packet):
    """
    Prints the IP and port information of the packet if it's IP-based.
    """
    if IP in packet:
        ip_layer = packet[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        protocol = "TCP" if TCP in packet else "UDP" if UDP in packet else "Other"
        
        # Get ports if TCP/UDP
        if TCP in packet or UDP in packet:
            src_port = packet[TCP].sport if TCP in packet else packet[UDP].sport
            dst_port = packet[TCP].dport if TCP in packet else packet[UDP].dport
        else:
            src_port = dst_port = "N/A"
        
        print(f"Packet Info: Src IP: {src_ip}, Dst IP: {dst_ip}, Protocol: {protocol}, "
              f"Src Port: {src_port}, Dst Port: {dst_port}")
    else:
        print("Non-IP Packet")

def relay_packet(packet):
    """
    Forwards the packet to the opposite interface.
    """
    # Print packet information
    print_packet_info(packet)

    # Determine which interface to send the packet to
    outgoing_iface = INTERFACE_OUTBOUND if packet.sniffed_on == INTERFACE_INBOUND else INTERFACE_INBOUND

    # Send the packet to the opposite interface
    sendp(packet, iface=outgoing_iface, verbose=False)

# Run the sniffing loop indefinitely with BPF filter
while True:
    sniff(iface=[INTERFACE_INBOUND, INTERFACE_OUTBOUND], prn=relay_packet, store=0, filter=BPF_FILTER)
