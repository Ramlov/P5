import os
import time
import subprocess

# Configuration
BRIDGE_NAME = "br0"
INTERFACE1 = "eth0"
INTERFACE2 = "eth1"
CONFIG_FILE = "/etc/network_latency_config.txt"
latency = 50  # Default latency in ms

def setup_bridge():
    # Remove any existing bridge if necessary
    os.system(f"ip link set {BRIDGE_NAME} down 2>/dev/null")
    os.system(f"ip link del {BRIDGE_NAME} type bridge 2>/dev/null")

    # Bring up the interfaces
    os.system(f"ifconfig {INTERFACE1} up")
    os.system(f"ifconfig {INTERFACE2} up")
    
    # Create and set up the bridge
    os.system(f"ip link add {BRIDGE_NAME} type bridge")
    os.system(f"ip link set {BRIDGE_NAME} up")
    
    # Add interfaces to the bridge
    os.system(f"ip link set dev {INTERFACE1} master {BRIDGE_NAME}")
    os.system(f"ip link set dev {INTERFACE2} master {BRIDGE_NAME}")
    
    # Remove any IP assigned to INTERFACE1
    os.system(f"ifconfig {INTERFACE1} 0.0.0.0")
    
    # Assign an IP to the bridge using DHCP
    os.system(f"dhclient {BRIDGE_NAME}")

def set_latency(latency_ms):
    # Clear any existing latency settings, ignoring errors if qdisc does not exist
    os.system(f"tc qdisc del dev {INTERFACE1} root 2>/dev/null")
    os.system(f"tc qdisc del dev {INTERFACE2} root 2>/dev/null")

    # Set the latency
    os.system(f"tc qdisc add dev {INTERFACE1} root netem delay {latency_ms}ms")
    os.system(f"tc qdisc add dev {INTERFACE2} root netem delay {latency_ms}ms")
    print(f"Latency of {latency_ms}ms applied to both {INTERFACE1} and {INTERFACE2}")


def main():
    # Setup network bridge
    setup_bridge()
    
    # Apply latency
    set_latency(latency)

if __name__ == "__main__":
    main()
