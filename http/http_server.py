"""
Very simple HTTP server.
"""

import socket
from datetime import datetime
from io import BufferedReader
from typing import Tuple

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
SUPPORTED_VERSIONS = [
    "HTTP/1.1",
]


class Request:
    def __init__(
        self,
        method: str,
        target: str,
        version: str,
        headers: dict,
        request_file: BufferedReader,
        client_address: Tuple[str, int],
    ):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.request_file = request_file
        self.client_host, self.client_port = client_address

    def __str__(self):
        return (
            f"<Request: {self.client_host}:{self.client_port} {self.method} {self.target} {self.version} "
            f"{self.headers}>"
        )


def serve_forever(host: str, port: int):
    """
    Infinitely acccept client connections and process requests.
    :param host: HTTP server host
    :param port: HTTP server port
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)

    try:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"HTTP server waiting for connection on {host}:{port}")

        while True:
            connection, (client_host, client_port) = server_socket.accept()
            print(datetime.now(), f"{client_host}:{client_port} connected...")

            try:
                serve_client(connection, (client_host, client_port))
            except Exception as ex:
                print("Failed to serve client", ex)
    finally:
        server_socket.close()


def serve_client(connection: socket.socket, client_address: Tuple[str, int]):
    try:
        request = parse_request(connection, client_address)
        print(datetime.now(), request)
        response = handle_request(request)
        send_response(connection, response)
    except ConnectionResetError:
        connection = None
    except Exception as ex:
        send_error(connection, ex)

    if connection:
        connection.close()


def parse_request_line(request_file: BufferedReader) -> Tuple[str, str, str]:
    """
    Parse request line into HTTP method, target, and HTTP version.

    Reference:
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages#request_line
    :return: tuple of HTTP method, target, and HTTP version
    """
    line_bytes = request_file.readline()
    request_line = str(line_bytes, "iso-8859-1").rstrip("\r\n")
    tokens = request_line.split(" ")

    # Expect exactly three tokens in request line - method, target, version:
    if len(tokens) != 3:
        raise Exception(f"Wrong request line: {request_line}")

    method, target, version = tokens
    return method, target, version


def parse_request_headers(request_file: BufferedReader) -> dict:
    """
    Simplified HTTP header parser. Does not take into account multiple headers with same names.

    Reference:
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages#headers
    :return: dict of header names and values
    """
    header_lines = []
    while True:
        line = request_file.readline()
        # Empty line means the end of headers:
        if line in (b"\r\n", b"\n", b""):
            break
        header_lines.append(line)

    headers = {}
    for header in header_lines:
        header = header.decode("iso-8859-1")
        key, value = header.split(":", 1)
        headers[key] = value.rstrip("\r\n").lstrip()

    return headers


def parse_request(
    connection: socket.socket,
    client_address: Tuple[str, int],
) -> Request:
    """
    Parse all neded data from request message into `Request` instance.

    References:
     - https://docs.python.org/3/library/socket.html#socket.socket.makefile
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages
    :param connection: client connection socket
    :param client_address: tuple of client host and port
    :return: filled `Request` instance
    """
    # Represent socket connection as file-like object:
    request_file = connection.makefile("rb")

    method, target, version = parse_request_line(request_file)
    if version not in SUPPORTED_VERSIONS:
        raise Exception(f"Unsupported HTTP version: {version}")

    headers = parse_request_headers(request_file)

    return Request(method, target, version, headers, request_file, client_address)


def handle_request(request): ...


def send_response(connection: socket.socket, response): ...


def send_error(connection: socket.socket, error): ...


if __name__ == "__main__":
    try:
        serve_forever(DEFAULT_HOST, DEFAULT_PORT)
    except KeyboardInterrupt:
        ...
