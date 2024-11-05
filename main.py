# main.py

import asyncio
import logging
from multiprocessing import Manager
import threading

# Import the modules
from bulkreceiver import start_bulk_upload_server
from requestreceiver import start_backend_request_server
from activemonitor import start_active_monitoring
from passivemonitor import start_passive_monitoring

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize the shared data structure using a Manager for cross-process sharing
    manager = Manager()
    field_devices = manager.dict()

    # Example field devices (populate as needed)
    field_devices.update({
        '192.168.1.100': {
            'latency': None,
            'packet_loss': None,
            'throughput': None,
            'status': 'Unknown',
            'last_active': None,
            'region': 'RegionA',
            'connection_stability': 0,
            # 'priority': 'normal',  # Optional field for priority
        },
        # Add other field devices as needed
    })

    # Start the event loop
    loop = asyncio.get_event_loop()

    # Start the servers
    loop.run_until_complete(start_bulk_upload_server(field_devices))
    loop.run_until_complete(start_backend_request_server(field_devices))

    # Start the monitoring modules
    # Active Monitoring
    active_monitoring_thread = threading.Thread(
        target=start_active_monitoring, args=(field_devices,), daemon=True
    )
    active_monitoring_thread.start()

    # Passive Monitoring
    passive_monitoring_process = start_passive_monitoring(field_devices)

    # Run the event loop forever
    try:
        logging.info("System initialization complete. Running event loop...")
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        # Clean up
        passive_monitoring_process.terminate()
        loop.close()

if __name__ == '__main__':
    main()
