"""
Very simple client to test with echo_server.py.
"""

import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("127.0.0.1", 53210))
client_socket.sendall(b"Hello, internet world!")

data = client_socket.recv(1024)
client_socket.close()

print("Data received:", repr(data))
