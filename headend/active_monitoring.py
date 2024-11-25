# active_monitoring.py

import threading
import time
import asyncio
from datetime import datetime, timedelta
from ping3 import ping
import websockets
import json
import ntplib

class ActiveMonitoring:
    """Maintains a set number of threads that perform active monitoring on assigned FDs."""

    def __init__(self, field_devices, fd_locks, num_threads):
        self.field_devices = field_devices
        self.fd_locks = fd_locks
        self.num_threads = num_threads
        self.active_threads = []
        self.stop_event = threading.Event()
        self.field_device_ids = list(self.field_devices.keys())
        self.time_monitoring_cycle = 10 #Time in seconds between cycles
        self.ntp_offset = self.get_ntp_offset()

    def get_ntp_offset(self):
        """
        Fetch NTP time offset to synchronize timing.
        """
        try:
            client = ntplib.NTPClient()
            response = client.request("pool.ntp.org")
            return response.offset
        except Exception as e:
            print(f"Failed to fetch NTP time: {e}")
            return 0
        
    def get_ntp_time(self):
        """
        Get current time synchronized with NTP (as a datetime object).
        """
        return datetime.now() + timedelta(seconds=self.ntp_offset)

    def start(self):
        # Calculate the number of field devices per thread
        fd_ids = self.field_device_ids
        total_fds = len(fd_ids)
        fd_range_general = total_fds // self.num_threads
        fd_range_rest = total_fds % self.num_threads

        # Create ranges for each thread
        fd_ranges = []
        start_index = 0
        for i in range(self.num_threads):
            if i == self.num_threads - 1:
                # Last thread gets the rest
                end_index = start_index + fd_range_general + fd_range_rest
            else:
                end_index = start_index + fd_range_general
            fd_ranges.append((start_index, end_index))
            start_index = end_index  # Update start_index without adding 1

        # Start threads with their assigned FDs
        for i, (start, end) in enumerate(fd_ranges):
            fd_ids_subset = fd_ids[start:end]
            t = threading.Thread(target=self.monitor_fds_subset, args=(fd_ids_subset,), daemon=True)
            t.start()
            self.active_threads.append(t)
            print(f"Thread {i+1} is monitoring field devices {start} to {end - 1}\n")


    def monitor_fds_subset(self, fd_ids_subset):
        print(f"Monitoring subset for {fd_ids_subset}")
        while not self.stop_event.is_set():
            for fd_id in fd_ids_subset:
                self.active_monitoring_cycle(fd_id)
            # Sleep before starting the next monitoring cycle
            time.sleep(self.time_monitoring_cycle)

    def active_monitoring_cycle(self, fd_id):
        #print(f"Started Monitoring on Field Device {fd_id}\n")
        fd_info = self.field_devices.get(fd_id)
        if not fd_info:
            print(f"FD {fd_id} not found in field_devices.")
            return

        ip_address = fd_info['ip_address']
        port = fd_info.get('port')

        # Step 1: Ping & ICMP Testing
        latency, packet_loss = self.ping_icmp_test(ip_address)

        # Step 2: Throughput Testing using WebSockets
        throughput = asyncio.run(self.throughput_test(ip_address, port))
        if throughput is None:
            # Set throughput to 0 if testing failed
            throughput = 0.0

        # Step 3: Classify connection
        status = self.classify_connection(latency, packet_loss, throughput)

        # Step 4: Analysis & Storage of Results
        with self.fd_locks[fd_id]:
            self.analyze_and_store_results(fd_info, fd_id, latency, packet_loss, throughput, status)

    def ping_icmp_test(self, ip_address, count=5, timeout=2):
        """Measure latency and packet loss using ICMP echo requests (ping)."""
        latencies = []
        successful_pings = 0

        for _ in range(count):
            try:
                latency = ping(ip_address, timeout=timeout, unit='ms')
                if latency is not None:
                    latencies.append(latency)  # Latency is already in milliseconds
                    successful_pings += 1
            except Exception as e:
                print(f"Ping to {ip_address} failed: {e}")

        if successful_pings > 0:
            avg_latency = sum(latencies) / successful_pings
            packet_loss = ((count - successful_pings) / count) * 100  # Percentage
        else:
            avg_latency = None  # No successful pings
            packet_loss = 100.0

        return avg_latency, packet_loss


    async def throughput_test(self, ip_address, port=80, data_size=1024 * 10, iterations=10):
        """Estimate throughput by sending and receiving data over WebSocket using NTP timestamps."""
        try:
            uri = f"ws://{ip_address}:{port}"
            total_data_sent = 0
            total_forward_delay = 0
            data_to_send = 'a' * data_size  # Sending 10 KB of data

            async with websockets.connect(uri, timeout=5) as websocket:
                for seq_num in range(iterations):
                    client_start_time = self.get_ntp_time() # NTP-synchronized time
                    await websocket.send(data_to_send)
                    # Receive acknowledgment with device timestamp
                    ack_message = await websocket.recv()

                    # Process acknowledgment message
                    ack_data = json.loads(ack_message)
                    device_recv_time = float(ack_data['timestamp'])

                    # Calculate forward delay
                    forward_delay = device_recv_time - client_start_time
                    total_forward_delay += forward_delay
                    total_data_sent += len(data_to_send.encode('utf-8'))

            # Average forward delay
            average_forward_delay = total_forward_delay / iterations

            # Calculate throughput in kbps
            if average_forward_delay > 0:
                throughput = (data_to_send * 8) / (average_forward_delay * 1000)  # kbps
            else:
                throughput = None
            return throughput
        except Exception as e:
            return None

    def classify_connection(self, latency, packet_loss, throughput):
        """Classify the connection based on latency, packet loss, and throughput."""
        if latency is None or packet_loss == 100.0 or throughput == 0:
            return 'Unavailable'

        if latency < 200 and packet_loss == 0 and throughput >= 500:
            return 'Good'
        elif latency <= 350 and packet_loss <= 20 and throughput >= 100:
            return 'Acceptable'
        else:
            return 'Poor'  # Default to 'Poor' if none of the above conditions match

    def analyze_and_store_results(self, fd_info, fd_id, latency, packet_loss, throughput, status):
        """Store results in the fd_info."""
        timestamp = datetime.now()

        # Update the fd_info dictionary
        active_metrics = fd_info.get('active_metrics', {})
        active_metrics['latency'] = latency
        active_metrics['packet_loss'] = packet_loss
        active_metrics['throughput'] = throughput
        active_metrics['status'] = status
        active_metrics['last_active'] = timestamp
        fd_info['active_metrics'] = active_metrics

        # Logging for verification
        ip_address = fd_info['ip_address']
        print(f"[{timestamp}] FD: {fd_id} (IP: {ip_address}) | Latency: {latency if latency is not None else 'N/A'} ms | Packet Loss: {packet_loss}% | Throughput: {throughput if throughput is not None else 'N/A'} kbps | Status: {status}\n")

    def stop(self):
        """Stops the active monitoring threads."""
        self.stop_event.set()
        for t in self.active_threads:
            t.join()
