#!/bin/env python
import asyncio
import websockets
from datetime import datetime
from scapy.all import sniff, TCP, IP

SERVER_HOST = "192.168.1.6"
SERVER_PORT = 8769

seq_number = None

def packet_callback(pkt):
    global seq_number
    if TCP in pkt and IP in pkt:
        seq_number = pkt[TCP].seq

async def send_messages():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        try:
            while True:
                send_time = datetime.utcnow()
                if seq_number is not None:
                    message = f"Seq {seq_number} | Hello from client | Sent at {send_time}"
                else:
                    message = f"Hello from client | Sent at {send_time}"
                await websocket.send(message)
                print(f"Sent to server at {send_time}: {message}")

                ack = await websocket.recv()
                receive_time = datetime.utcnow()
                print(f"Received from server at {receive_time}: {ack}")

                latency = (receive_time - send_time).total_seconds() * 1000  # in milliseconds
                print(f"Latency: {latency:.2f} ms")

                await asyncio.sleep(10)
        except websockets.exceptions.ConnectionClosedError:
            print("Server disconnected")
        finally:
            print("Connection closed")

if __name__ == "__main__":
    # Start packet sniffing in a separate thread
    import threading
    sniff_thread = threading.Thread(target=sniff, kwargs={'prn': packet_callback, 'filter': 'tcp', 'store': 0})
    sniff_thread.daemon = True
    sniff_thread.start()

    # Run the asyncio event loop
    asyncio.run(send_messages())