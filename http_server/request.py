"""
Request-related code.
"""

import os.path
import socket
from io import BufferedReader
from typing import Tuple
from urllib.parse import ParseResult, parse_qs, urlparse

import settings
from exceptions import HTTPError


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

    @property
    def content_type(self) -> str:
        """
        Return MIME type based on file extension in request path.

        :return: MIME type based on file extension, or `DEFAULT_CONTENT_TYPE`
        """
        _, extension = os.path.splitext(self.path)
        content_type = settings.EXTENSION_TO_MIME_TYPE.get(
            extension, settings.DEFAULT_CONTENT_TYPE
        )
        return content_type


def parse_request(connection: socket.socket) -> Request:
    """
    Parse all neded data from request message into `Request` instance.

    References:
     - https://docs.python.org/3/library/socket.html#socket.socket.makefile
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages
    :param connection: client connection socket
    :return: filled `Request` instance
    """
    # Represent socket connection as file-like object:
    request_file = connection.makefile("rb")

    method, target, version = _parse_request_line(request_file)
    if version not in settings.SUPPORTED_VERSIONS:
        raise Exception(f"Unsupported HTTP version: {version}")

    headers = _parse_request_headers(request_file)

    # Check `Hosts` header
    if not headers.get("Host"):
        raise HTTPError(400, "Bad request")

    if headers.get("Host") not in settings.ALLOWED_HOSTS:
        raise HTTPError(404, "Not found")

    client_address = connection.getpeername()
    return Request(method, target, version, headers, request_file, client_address)


def _parse_request_line(request_file: BufferedReader) -> Tuple[str, str, str]:
    """
    Parse request line into HTTP method, target, and HTTP version tuple.

    Reference:
     - https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages#request_line
    :return: tuple of HTTP method, target, and HTTP version
    """
    line_bytes = request_file.readline()
    request_line = str(line_bytes, settings.HEADER_ENCODING).rstrip("\r\n")
    tokens = request_line.split(" ")

    # Expect exactly three tokens in request line - method, target, version:
    if len(tokens) != 3:
        raise Exception(f"Wrong request line: {request_line}")

    method, target, version = tokens
    return method, target, version


def _parse_request_headers(request_file: BufferedReader) -> dict:
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
        header = header.decode(settings.HEADER_ENCODING)
        key, value = header.split(":", 1)
        headers[key] = value.rstrip("\r\n").lstrip()

    return headers
