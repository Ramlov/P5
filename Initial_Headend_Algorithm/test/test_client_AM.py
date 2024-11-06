# test_active_monitoring.py

from AM import ActiveMonitoring
import time

# Initialize ActiveMonitoring instance
monitor = ActiveMonitoring()

# Step 2: Run ICMP ping test for latency and packet loss
fd_address = "127.0.0.1"
latency, packet_loss = monitor.ping_icmp_test(fd_address)
print(f"ICMP Test - Latency: {latency:.2f} ms, Packet Loss: {packet_loss:.2f}%")

# Step 4: Run throughput test to local TCP server
throughput = monitor.throughput_test(fd_address, port=8080)
print(f"Throughput Test - Throughput: {throughput:.2f} KBps")

# Step 6: Run continuous monitoring for multiple FDs
field_devices = [
    {"address": "127.0.0.1", "port": 8080},   # Local TCP server
    {"address": "192.0.2.1", "port": 8080}    # Non-routable IP to test failure
]
monitor.monitor_all_fds(field_devices, wait_period=10)
