# bulkreceiver.py

import asyncio
import websockets
import logging
from datetime import datetime

async def handle_bulk_upload(websocket, path, field_devices):
    try:
        # Get the IP address of the connected field device
        device_ip = websocket.remote_address[0]
        logging.info(f"Bulk upload connection established with {device_ip}")

        # Receive data from the field device
        data = await websocket.recv()
        logging.info(f"Received bulk data from {device_ip}")

        # Process the received data
        process_bulk_data(device_ip, data, field_devices)

        # Update the last_active timestamp and connection stability
        if device_ip in field_devices:
            field_devices[device_ip]['last_active'] = datetime.now()
            field_devices[device_ip]['connection_stability'] += 1
            # Optionally update status
            field_devices[device_ip]['status'] = 'Good'  # Update as appropriate

        # Optionally send an acknowledgment back to the field device
        await websocket.send("Bulk data received successfully.")

    except Exception as e:
        logging.error(f"Error handling bulk upload from {device_ip}: {e}")
        # Update connection stability
        if device_ip in field_devices:
            field_devices[device_ip]['connection_stability'] -= 1

def process_bulk_data(device_ip, data, field_devices):
    # Implement your data processing logic here
    # For example, parse the data and store it in a database or file
    # This is a placeholder function
    logging.info(f"Processing bulk data from {device_ip}: {data[:50]}...")  # Log first 50 chars

async def start_bulk_upload_server(field_devices):
    server = await websockets.serve(
        lambda ws, path: handle_bulk_upload(ws, path, field_devices),
        '0.0.0.0', 8765
    )
    logging.info("Bulk Upload Server started on port 8765")
    return server
