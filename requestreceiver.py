# requestreceiver.py

import asyncio
import websockets
import json
import logging

async def handle_backend_request(websocket, path, field_devices):
    try:
        logging.info("Backend request connection established")

        # Receive request data from the backend
        request_data = await websocket.recv()
        logging.info(f"Received backend request: {request_data}")

        # Parse the request (assuming JSON format)
        request = json.loads(request_data)

        # Process the request based on its type
        await process_backend_request(request, field_devices)

        # Optionally send a response back to the backend
        response = {"status": "success", "message": "Request processed successfully."}
        await websocket.send(json.dumps(response))

    except Exception as e:
        logging.error(f"Error handling backend request: {e}")
        # Optionally send an error response back to the backend
        response = {"status": "error", "message": str(e)}
        await websocket.send(json.dumps(response))

async def process_backend_request(request, field_devices):
    # Implement your request processing logic here
    request_type = request.get('type')

    if request_type == 'region_priority':
        region = request.get('region')
        if region:
            logging.info(f"Processing region priority request for region: {region}")
            # Update adaptive data access priorities based on the region
            await prioritize_region(region, field_devices)
        else:
            logging.warning("Region not specified in the request.")

    elif request_type == 'device_priority':
        devices = request.get('devices')
        if devices:
            logging.info(f"Processing device priority request for devices: {devices}")
            # Update adaptive data access priorities based on the device list
            await prioritize_devices(devices, field_devices)
        else:
            logging.warning("Devices not specified in the request.")

    else:
        logging.warning(f"Unknown request type: {request_type}")

async def prioritize_region(region, field_devices):
    # Implement logic to prioritize devices in the specified region
    for ip, info in field_devices.items():
        if info.get('region') == region:
            info['priority'] = 'high'  # Set a priority flag or adjust selection logic
            logging.info(f"Set priority to high for device {ip} in region {region}")

async def prioritize_devices(device_list, field_devices):
    # Implement logic to prioritize specific devices
    for ip in device_list:
        if ip in field_devices:
            field_devices[ip]['priority'] = 'high'  # Set a priority flag or adjust selection logic
            logging.info(f"Set priority to high for device {ip}")
        else:
            logging.warning(f"Device {ip} not found in field devices.")

async def start_backend_request_server(field_devices):
    server = await websockets.serve(
        lambda ws, path: handle_backend_request(ws, path, field_devices),
        '0.0.0.0', 5678
    )
    logging.info("Backend Request Server started on port 5678")
    return server
