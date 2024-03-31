"""
Basic WSGI application, should print out contents of `environ` dict as output.

Example usage:
    python wsgi_app.py
    curl -X GET http://127.0.0.1:8000/
"""

from typing import Callable, Iterable
from wsgiref.simple_server import make_server


def application(environ: dict, start_response: Callable) -> Iterable:
    body = [f"{key}: {value}" for key, value in sorted(environ.items())]
    body = "\n".join(body)
    status = "200 OK"
    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(body))),
    ]

    start_response(status, headers)

    # We must return iterable according to PEP 3333.
    # `body` must be converted to bytes for builtin WSGI server to work properly.
    return [body.encode()]


# Instantiate Python built-in WSGI server passing our application to it
server = make_server("localhost", 8000, application)

# Serve single request and quit
print("Waiting for single request on port 8000...")
server.handle_request()
