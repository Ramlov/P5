# simple_server.py
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 8080))
server.listen(1)
print("Server started on 127.0.0.1:8080")

while True:
    conn, addr = server.accept()
    print(f"Connection from {addr}")
    conn.sendall(b'ack')  # Send acknowledgment to simulate data exchange
    conn.close()
