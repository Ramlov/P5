#!/usr/bin/env python
import socket
import threading
import re
from datetime import datetime

SERVER_HOST = '192.168.1.4'
SERVER_PORT = 3456

def handle_client(client_socket, client_address):
    print(f"Client connected from {client_address}")
    try:
        while True:
            # Receive data from the client
            data = client_socket.recv(1024)
            if not data:
                # No more data from client
                break
            message = data.decode()
            received_time = datetime.utcnow()
            print(f"Received from client at {received_time}: {message}")

            # Extract the sequence number from the message
            seq_match = re.search(r"Seq (\d+)", message)
            if seq_match:
                seq_number = seq_match.group(1)
                print(f"Sequence Number: {seq_number}")

            # Send acknowledgment back to the client
            ack_message = f"Acknowledged: {message} | Received at {received_time}"
            client_socket.sendall(ack_message.encode())
    except ConnectionResetError:
        print("Client disconnected unexpectedly")
    finally:
        print("Connection closed")
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen()
    print(f"Server running on {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            # Accept a new client connection
            client_socket, client_address = server.accept()
            # Handle the client in a new thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down")
    finally:
        server.close()

if __name__ == "__main__":
    main()