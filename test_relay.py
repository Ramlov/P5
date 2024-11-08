from netfilterqueue import NetfilterQueue
from scapy.all import IP, send

def forward_packet(packet):
    """
    Forward packets received from NFQUEUE to the appropriate interface.
    """
    scapy_packet = IP(packet.get_payload())  # Convert the raw payload to a Scapy packet
    src_ip = scapy_packet.src
    dst_ip = scapy_packet.dst
    protocol = scapy_packet.proto

    # Display packet details
    print(f"Packet received: {src_ip} -> {dst_ip}, Protocol: {protocol}")

    # Accept the packet to let it continue through the stack
    packet.accept()

# Create an instance of NetfilterQueue and bind it to our forward_packet handler
nfqueue = NetfilterQueue()
nfqueue.bind(1, forward_packet)  # Bind to queue number 1

try:
    print("Starting packet forwarding...")
    nfqueue.run()
except KeyboardInterrupt:
    print("Stopping packet forwarding...")
finally:
    nfqueue.unbind()
