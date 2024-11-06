# passivemonitor.py

import multiprocessing
import logging

def passive_monitoring():
    logging.info("Passive monitoring is running (no flow analysis implemented).")
    # Placeholder for future implementation
    while True:
        pass  # Keep the process alive

def start_passive_monitoring(field_devices):
    # Start passive monitoring in a separate process
    monitoring_process = multiprocessing.Process(
        target=passive_monitoring, daemon=True
    )
    monitoring_process.start()

    # Return the process
    return monitoring_process
