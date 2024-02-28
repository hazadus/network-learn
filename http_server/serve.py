"""
Contains stuff related with main server loop - serve and handle client requests.
"""

import socket
from datetime import datetime

from exceptions import HTTPError
from request import Request, parse_request
from response import Response, load_path, send_error, send_response


def serve_forever(host: str, port: int):
    """
    Infinitely acccept client connections and process requests.

    :param host: HTTP server host
    :param port: HTTP server port
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"HTTP server waiting for connection on {host}:{port}")

        while True:
            connection, (client_host, client_port) = server_socket.accept()
            print(datetime.now(), f"{client_host}:{client_port} connected...")

            try:
                _serve_client(connection)
            except Exception as ex:
                print("Failed to serve client", ex)
    finally:
        server_socket.close()


def _serve_client(connection: socket.socket):
    """
    Process request, then send back the response.

    :param connection: client connection socket
    """
    try:
        request = parse_request(connection)
        print(datetime.now(), request)

        response = _handle_request(request)
        print(datetime.now(), response)

        send_response(connection, response)
    except ConnectionResetError:
        connection = None
    except Exception as ex:
        print(datetime.now(), "Error:", ex)
        send_error(connection, ex)

    if connection:
        connection.close()


def _handle_request(request: Request) -> Response:
    """
    Build `Response` instance depenging on `Request`.

    :param request: request to handle
    :return: filled `Response` instance
    """
    supported_methods = ["GET"]

    if request.method not in supported_methods:
        raise HTTPError(400, f"Method {request.method} is not supported.")

    return load_path(request)
