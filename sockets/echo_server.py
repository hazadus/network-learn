"""
Simple echo server.
Run `telnet 127.0.0.1 53210` to connect.
"""

import socket

server_socket = socket.socket(
    socket.AF_INET,  # Create network socket
    socket.SOCK_STREAM,  # Use TCP (SOCK_DGRAM for UDP)
    proto=0,  # Use IP protocol
)
# Make server socket accessible via all machine addresses (not only internal):
server_socket.bind(("", 53210))
# 10 is the max number of connected clients, awaiting response (backlog):
server_socket.listen(10)

while True:
    # Wait for incoming connection:
    print("Waiting for connection...")
    # Note that there's another socket created upon each connection:
    client_socket, client_address = server_socket.accept()
    print("Connection from:", client_address)

    while True:
        # Accept data in 1024-byte chunks:
        data = client_socket.recv(1024)
        # Exit loop when there's no more data from client:
        if not data:
            break
        # Send the received data back to client
        client_socket.sendall(data)

    client_socket.close()
