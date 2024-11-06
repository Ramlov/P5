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

async def main():
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

    # Start the servers
    bulk_server = await start_bulk_upload_server(field_devices)
    backend_server = await start_backend_request_server(field_devices)

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
        await asyncio.Event().wait()  # Keep the main coroutine running
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        # Clean up
        passive_monitoring_process.terminate()
        # Close servers
        bulk_server.close()
        backend_server.close()
        await bulk_server.wait_closed()
        await backend_server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
