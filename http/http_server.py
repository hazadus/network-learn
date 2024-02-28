"""
Very simple HTTP server.
Serves static files.
"""

import os.path
import socket
from datetime import datetime
from io import BufferedReader
from typing import Tuple
from urllib.parse import ParseResult, parse_qs, urlparse

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
SUPPORTED_VERSIONS = [
    "HTTP/1.1",
]
ALLOWED_HOSTS = [
    DEFAULT_HOST,
    f"{DEFAULT_HOST}:{DEFAULT_PORT}",
    "127.0.0.1",
    f"127.0.0.1:{DEFAULT_PORT}",
    "localhost",
    f"localhost:{DEFAULT_PORT}",
]
HEADER_ENCODING = "iso-8859-1"
STATIC_ROOT = "./static"
STATIC_DIR = os.path.abspath(STATIC_ROOT)
EXTENSION_TO_MIME_TYPE = {
    ".htm": "text/html; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".png": "image/png",
    ".bin": "application/octet-stream",
    ".css": "text/css",
    ".csv": "text/csv",
    ".gif": "image/gif",
    ".ico": "image/vnd.microsoft.icon",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".js": "text/javascript",
    ".json": "application/json",
    ".mp3": "audio/mpeg",
    ".mp4": "vide/mp4",
    ".otf": "font/otf",
    ".pdf": "application/pdf",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
}
DEFAULT_CONTENT_TYPE = "application/octet-stream"


class Request:
    """
    Represents HTTP Request.

    References:
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages#http_requests
    """

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

    @property
    def url(self) -> ParseResult:
        return urlparse(self.target)

    @property
    def path(self) -> str:
        return self.url.path

    @property
    def query(self) -> dict[str, list[str]]:
        return parse_qs(self.url.query)


class Response:
    """
    Represents HTTP Response.

    References:
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages#http_responses
    """

    def __init__(
        self,
        status: int,
        reason: str,
        headers: dict | None = None,
        body: bytes | None = None,
    ):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def __str__(self):
        return (
            f"<Response: [{self.status}] {self.reason} {self.headers} "
            f"Body length: {0 if self.body is None else len(self.body)}>"
        )


class HTTPError(Exception):
    def __init__(self, status: int, reason: str, body: bytes | None = None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


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
        print(datetime.now(), response)

        send_response(connection, response)
    except ConnectionResetError:
        connection = None
    except Exception as ex:
        print(datetime.now(), "Error:", ex)
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
    request_line = str(line_bytes, HEADER_ENCODING).rstrip("\r\n")
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
        header = header.decode(HEADER_ENCODING)
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

    # Check `Hosts` header
    if not headers.get("Host"):
        raise HTTPError(400, "Bad request")

    if headers.get("Host") not in ALLOWED_HOSTS:
        raise HTTPError(404, "Not found")

    return Request(method, target, version, headers, request_file, client_address)


def get_content_type(request: Request) -> str:
    """
    Return MIME type based on file extension in request path.

    :param request: Request to process
    :return: MIME type based on file extension, or `DEFAULT_CONTENT_TYPE`
    """
    _, extension = os.path.splitext(request.path)
    content_type = EXTENSION_TO_MIME_TYPE.get(extension, DEFAULT_CONTENT_TYPE)
    return content_type


def load_static_file(request: Request) -> Response:
    """
    Load static file into Response instance.

    :param request: Request instance to process
    :return: Response instance properly initialized with required data
    :raise HTTPError: 404 error if file not found
    """
    path = os.path.sep.join([STATIC_DIR, request.path])

    try:
        with open(path, "rb") as file:
            body = file.read()
    except Exception as ex:
        raise HTTPError(404, f"Not found. {ex}")

    headers = {
        "Content-Type": get_content_type(request),
        "Content-Length": len(body),
    }

    return Response(200, "OK", headers=headers, body=body)


def load_directory_listing(request: Request) -> Response:
    """
    Create `Response` with directory listing.

    :param request: request to handle
    :return: `Response` instance with directory listing
    """
    host = request.headers.get("Host")
    path = os.path.sep.join([STATIC_DIR, request.path])
    listing = ""

    for filename in os.listdir(path):
        listing += (
            f'<li><a href="{os.path.join(request.path, filename)}">{filename}</a></li>'
        )

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>Directory listing</title>
        </head>
        
        <body>
          <h1>{host}{request.path}</h1>
          <ul>{listing}</ul>
        </body>
    </html>
    """

    headers = {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": len(html),
    }
    return Response(200, "OK", headers=headers, body=html.encode("utf-8"))


def load_path(request: Request) -> Response:
    """
    Load static file or directory listing, depending on request.

    :param request: request to handle
    :return: `Response` instance filled with static file or directory listing
    """
    path = os.path.sep.join([STATIC_DIR, request.path])

    # Ensure that the path exists, and user can't break out of our base directory:
    if not path.startswith(STATIC_DIR) or not os.path.exists(path):
        raise HTTPError(404, "Not found")

    if os.path.isfile(path):
        return load_static_file(request)

    if os.path.isdir(path):
        return load_directory_listing(request)


def handle_request(request: Request) -> Response:
    """
    Build `Response` instance depenging on `Request`.

    :param request: request to handle
    :return: filled `Response` instance
    """
    supported_methods = ["GET"]

    if request.method not in supported_methods:
        raise HTTPError(400, f"Method {request.method} is not supported.")

    return load_path(request)


def send_response(connection: socket.socket, response: Response):
    """
    Serialize `Response` instance to proper HTTP response format and write it to client socket.

    Reference:
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages#http_responses
    :param connection: client socket connection to send response to
    :param response: `Response` instance to send
    """
    response_file = connection.makefile("wb")

    # Write HTTP status line
    status_line = f"HTTP/1.1 {response.status} {response.reason}\r\n"
    response_file.write(status_line.encode(HEADER_ENCODING))

    # Write all response headers
    if response.headers:
        for key, value in response.headers.items():
            header_line = f"{key}: {value}\r\n"
            response_file.write(header_line.encode(HEADER_ENCODING))

    # Empty line means the end of headers
    response_file.write(b"\r\n")

    # Write the body, if present
    if response.body:
        response_file.write(response.body)

    response_file.flush()
    response_file.close()


def send_error(connection: socket.socket, error: HTTPError):
    try:
        status = error.status
        reason = error.reason
        body = (error.body or error.reason).encode("utf-8")
    except:
        status = 500
        reason = "Internal Server Error"
        body = b"Internal Server Error"
    response = Response(status, reason, {"Content-Length": len(body)}, body)
    send_response(connection, response)


if __name__ == "__main__":
    try:
        serve_forever(DEFAULT_HOST, DEFAULT_PORT)
    except KeyboardInterrupt:
        ...
