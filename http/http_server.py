"""
Very simple HTTP server.
"""

import socket


def serve_forever(host: str, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)

    try:
        server_socket.bind((host, port))
        server_socket.listen()

        while True:
            connection, _ = server_socket.accept()

            try:
                serve_client(connection)
            except Exception as ex:
                print("Failed to serve client", ex)
    finally:
        server_socket.close()


def serve_client(connection: socket.socket):
    try:
        request = parse_request(connection)
        response = handle_request(request)
        send_response(connection, response)
    except ConnectionResetError:
        connection = None
    except Exception as ex:
        send_error(connection, ex)

    if connection:
        connection.close()


def parse_request(connection: socket.socket): ...


def handle_request(request): ...


def send_response(connection: socket.socket, response): ...


def send_error(connection: socket.socket, error): ...


if __name__ == "__main__":
    try:
        serve_forever("0.0.0.0", 8000)
    except KeyboardInterrupt:
        ...
