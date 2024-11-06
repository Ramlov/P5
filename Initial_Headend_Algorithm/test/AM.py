# active_monitoring.py

import ping3
import socket
import time
from datetime import datetime

class ActiveMonitoring:
    """Performs active network monitoring with Ping, ICMP, and Throughput Testing."""

    def __init__(self):
        self.results = {}

    def ping_icmp_test(self, fd_address, count=5):
        """Measure latency and packet loss using ICMP echo requests (ping)."""
        latencies = []
        successful_pings = 0

        for _ in range(count):
            latency = ping3.ping(fd_address)
            if latency is not None:
                latencies.append(latency * 1000)  # Convert to ms
                successful_pings += 1

        if successful_pings > 0:
            avg_latency = sum(latencies) / successful_pings
            packet_loss = (count - successful_pings) / count * 100
        else:
            avg_latency = float('inf')  # No successful pings
            packet_loss = 100.0

        return avg_latency, packet_loss

    def throughput_test(self, fd_address, port=8080, data_size=1024):
        """Measure throughput by sending data to the target FD."""
        try:
            start_time = time.time()
            with socket.create_connection((fd_address, port), timeout=1) as s:
                s.sendall(b'a' * data_size)  # Send dummy data
                s.recv(1024)  # Receive dummy data for throughput completion
            throughput = data_size / (time.time() - start_time) / 1024  # Throughput in KBps
        except Exception:
            throughput = 0  # No throughput if connection fails

        return throughput

    def analyze_and_store_results(self, fd_address, latency, packet_loss, throughput):
        """Analyze and store results for adaptive data access."""
        timestamp = datetime.now()
        status = "Good" if latency < 200 and packet_loss < 1 and throughput > 500 else "Acceptable" if latency < 500 and packet_loss < 5 else "Poor"
        
        # Store the results in a dictionary (or alternatively, in a database or file)
        self.results[fd_address] = {
            "timestamp": timestamp,
            "latency": latency,
            "packet_loss": packet_loss,
            "throughput": throughput,
            "status": status
        }

        # Logging for verification
        print(f"[{timestamp}] FD: {fd_address} | Latency: {latency:.2f} ms | Packet Loss: {packet_loss:.2f}% | Throughput: {throughput:.2f} KBps | Status: {status}")

    def active_monitoring_cycle(self, fd_address):
        """Run a full monitoring cycle for one FD."""
        # Step 1: Ping & ICMP Testing
        latency, packet_loss = self.ping_icmp_test(fd_address)

        # Step 2: Throughput Testing
        throughput = self.throughput_test(fd_address)

        # Step 3: Analysis & Storage of Results
        self.analyze_and_store_results(fd_address, latency, packet_loss, throughput)

    def monitor_all_fds(self, fds, wait_period=60):
        """Monitor all FDs in the list, with a wait period between each cycle."""
        for fd in fds:
            print(f"Starting active monitoring for FD: {fd['address']}")
            self.active_monitoring_cycle(fd['address'])
            time.sleep(wait_period)  # Wait period before moving to the next FD
