# main.py

import threading
import time
import sqlite3
import asyncio
import websockets

from multiprocessing import Manager

from active_monitoring import ActiveMonitoring
from passive_monitoring import PassiveMonitoring
from adaptive_data_access import AdaptiveDataAccess

def load_field_devices():
    conn = sqlite3.connect('field_devices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT FD_ID, IP, Region, Port, Last_Data_Received FROM field_devices')
    rows = cursor.fetchall()
    conn.close()

    manager = Manager()
    field_devices = manager.dict()
    fd_locks = {}

    for fd_id, ip_address, region, port, last_data_received in rows:
        fd_id = str(fd_id)  # Ensure FD_ID is a string
        field_devices[fd_id] = manager.dict({
            'ip_address': ip_address,
            'port': port,
            'region': region,
            'last_data_received': last_data_received,  # This can be None
            'active_metrics': manager.dict(),
            'passive_metrics': manager.dict(),  # Placeholder for now
        })
        fd_locks[fd_id] = threading.Lock()

    #print(f"{field_devices}\n \n \n {field_devices.items}")

    return field_devices, fd_locks

def backend_listener(adaptive_data_access, server_ip, backend_listen_port):
    async def handler(websocket):
        async for message in websocket:
            message = message.strip()
            if message.lower() == 'stop':
                print("Received 'stop' command from backend.\n")
                adaptive_data_access.stop_backend_focus()
            else:
                # Process the backend request
                # Assuming the message is a comma-separated list of FD IDs, e.g., "1,2,3"
                requested_fd_ids = message.split(',')
                requested_fd_ids = [fd_id.strip() for fd_id in requested_fd_ids]
                print(f"Received backend request to focus on FDs: {requested_fd_ids}\n")
                adaptive_data_access.focus_on_fds(requested_fd_ids)

    async def server():
        async with websockets.serve(handler, server_ip, backend_listen_port):
            await asyncio.Future()  # Run forever

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server())

def main():
    # Server Information
    server_ip = '192.168.1.10'
    passive_server_port = '31000'
    backend_listen_port = '8000'

    # Load field devices from SQLite database
    field_devices, fd_locks = load_field_devices()

    # Initialize the Passive Monitoring module (placeholder)
    passive_monitor = PassiveMonitoring(field_devices=field_devices, fd_locks=fd_locks, host=server_ip, port=passive_server_port)
    passive_monitor.start()

    # Initialize the Adaptive Data Access module
    #adaptive_data_access = AdaptiveDataAccess(field_devices, fd_locks)
    #adaptive_data_access_thread = threading.Thread(target=adaptive_data_access.run, daemon=True)
    #adaptive_data_access_thread.start()

    # Start the backend listener in a separate thread
    #backend_listener_thread = threading.Thread(target=backend_listener, args=(adaptive_data_access, server_ip, backend_listen_port,), daemon=True)
    #backend_listener_thread.start()

    # Initialize and start Active Monitoring
    num_active_threads = 3  # Adjust as needed
    active_monitor = ActiveMonitoring(field_devices, fd_locks, num_active_threads)
    active_monitor.start()


    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == '__main__':
    main()
