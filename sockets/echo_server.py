"""
Simple echo server.
Run `telnet 127.0.0.1 53210` to connect.
"""
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
server_socket.bind(("", 53210))
server_socket.listen(10)

while True:
    client_socket, client_address = server_socket.accept()
    print("Connection from:", client_address)

    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        client_socket.sendall(data)

    client_socket.close()
