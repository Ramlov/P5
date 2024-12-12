import sqlite3
import asyncio
import websockets
import random
import time

# Connect to the SQLite database
conn = sqlite3.connect('field_devices.db')
cursor = conn.cursor()

# Fetch all field device IDs from the databases
cursor.execute("SELECT FD_ID FROM field_devices")
all_fd_ids = [row[0] for row in cursor.fetchall()]

# Shuffle the list of field device IDs for random selection
#random.shuffle(all_fd_ids)

async def fetch_data_from_device(fd_id):
    # Retrieve field device details
    cursor.execute("SELECT IP, Port FROM field_devices WHERE FD_ID = ?", (fd_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"Field device {fd_id} not found.")
        return

    ip, port = result
    uri = f"ws://{ip}:{port}"  # Assuming the device supports WebSocket communication
    print(f"Attempting to fetch data from FD {fd_id} at {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send("FETCH_DATA")
            response = await websocket.recv()
            print(f"Data received from FD {fd_id}")

    except Exception as e:
        print(f"Error fetching data from FD {fd_id}: {e}")

async def main():
    start_time = time.time()
    for fd_id in all_fd_ids:
        await fetch_data_from_device(fd_id)

    print("Data fetching completed for all field devices.")
    print(f"Runtime: {time.time() - start_time}")

# Run the asyncio event loop
asyncio.run(main())

# Close the database connection
conn.close()
