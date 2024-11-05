# activemonitor.py

import threading
import time
from ping3 import ping
import logging

def classify_connection(device_info):
    # Implement classification logic based on latency, packet loss, etc.
    latency = device_info.get('latency')
    packet_loss = device_info.get('packet_loss')
    if latency is not None and latency < 100 and packet_loss < 1:
        return 'Good'
    elif latency is not None and latency < 300 and packet_loss < 5:
        return 'Moderate'
    else:
        return 'Poor'

def tcp_probe(ip, port=8765, timeout=2):
    import socket
    try:
        start_time = time.time()
        sock = socket.create_connection((ip, port), timeout=timeout)
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        sock.close()
        return latency
    except Exception:
        return None

def calculate_packet_loss(ip, count=4, timeout=2):
    # Use ping3 to send multiple pings and calculate packet loss
    success = 0
    for _ in range(count):
        latency = ping(ip, timeout=timeout, unit='ms')
        if latency is not None:
            success += 1
    packet_loss = ((count - success) / count) * 100  # Percentage
    return packet_loss

def start_active_monitoring(field_devices):
    def active_monitoring():
        while True:
            for ip in field_devices.keys():
                # Attempt ICMP ping
                latency = ping(ip, timeout=2, unit='ms')
                if latency is None:
                    # Fallback to TCP probe
                    latency = tcp_probe(ip, port=8765)
                if latency is not None:
                    field_devices[ip]['latency'] = latency
                    field_devices[ip]['packet_loss'] = calculate_packet_loss(ip)
                    field_devices[ip]['connection_stability'] += 1
                    field_devices[ip]['status'] = classify_connection(field_devices[ip])
                    logging.info(f"Active monitoring updated for {ip}: {field_devices[ip]}")
                else:
                    field_devices[ip]['connection_stability'] -= 1
                    field_devices[ip]['status'] = 'Unavailable'
                    logging.warning(f"Device {ip} is unavailable.")
            time.sleep(900)  # Wait for 15 minutes

    # Start active monitoring in a separate thread
    monitoring_thread = threading.Thread(target=active_monitoring, daemon=True)
    monitoring_thread.start()
