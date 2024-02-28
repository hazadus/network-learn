"""
Response-related code.
"""

import os.path
import socket
import settings
from request import Request
from exceptions import HTTPError


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
    response_file.write(status_line.encode(settings.HEADER_ENCODING))

    # Write all response headers
    if response.headers:
        for key, value in response.headers.items():
            header_line = f"{key}: {value}\r\n"
            response_file.write(header_line.encode(settings.HEADER_ENCODING))

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


def load_path(request: Request) -> Response:
    """
    Load static file or directory listing, depending on request.

    :param request: request to handle
    :return: `Response` instance filled with static file or directory listing
    """
    path = os.path.sep.join([settings.STATIC_DIR, request.path])

    # Ensure that the path exists, and user can't break out of our base directory:
    if not path.startswith(settings.STATIC_DIR) or not os.path.exists(path):
        raise HTTPError(404, "Not found")

    if os.path.isfile(path):
        return _load_static_file(request)

    if os.path.isdir(path):
        return _load_directory_listing(request)


def _load_static_file(request: Request) -> Response:
    """
    Load static file into Response instance.

    :param request: Request instance to process
    :return: Response instance properly initialized with required data
    :raise HTTPError: 404 error if file not found
    """
    path = os.path.sep.join([settings.STATIC_DIR, request.path])

    try:
        with open(path, "rb") as file:
            body = file.read()
    except Exception as ex:
        raise HTTPError(404, f"Not found. {ex}")

    headers = {
        "Content-Type": request.content_type,
        "Content-Length": len(body),
    }

    return Response(200, "OK", headers=headers, body=body)


def _load_directory_listing(request: Request) -> Response:
    """
    Create `Response` with directory listing.

    :param request: request to handle
    :return: `Response` instance with directory listing
    """
    host = request.headers.get("Host")
    path = os.path.sep.join([settings.STATIC_DIR, request.path])
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
