"""
Usage example:
    python server.py routes:application
    curl -X GET http://127.0.0.1:8000/hello
    curl -X GET http://127.0.0.1:8000/hello/Alexander
"""

import io
import socket
import sys
from datetime import datetime
from email import utils


class WSGIServer:
    request_queue_size = 1

    def __init__(self, server_address):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(server_address)
        self.server_socket.listen(self.request_queue_size)

        host, port = self.server_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

        self.headers_set = []
        self.application = None
        self.client_connection = None
        self.request_data = None
        self.request_method = None
        self.path = None
        self.request_version = None

    def set_app(self, application_):
        self.application = application_

    def serve_forever(self):
        while True:
            self.client_connection, _ = self.server_socket.accept()
            self.handle_one_request()

    def handle_one_request(self):
        data = self.client_connection.recv(1024)
        self.request_data = data.decode("utf-8")

        # Print out formatted request data
        print("".join(f"< {line}\n" for line in self.request_data.splitlines()))

        self.parse_request(self.request_data)

        env = self.get_environ()

        # The magic is here: call WSGI application to get result and build response body
        result = self.application(env, self.start_response)

        # Build response and send it back to the client
        self.finish_response(result)

    def parse_request(self, request: str):
        # First line of the HTTP request, aka request line,
        # goes like "GET / HTTP/1.1\r\n"
        request_line = request.splitlines()[0]
        request_line = request_line.rstrip("\r\n")
        (self.request_method, self.path, self.request_version) = request_line.split()

    def get_environ(self) -> dict:
        env = {}
        # Required WSGI variables
        env["wsgi.version"] = (1, 0)
        env["wsgi.url_scheme"] = "http"
        env["wsgi.input"] = io.StringIO(self.request_data)
        env["wsgi.errors"] = sys.stderr
        env["wsgi.multithread"] = False
        env["wsgi.multiprocess"] = False
        env["wsgi.run_once"] = False
        # Required CGI variables
        env["REQUEST_METHOD"] = self.request_method
        env["PATH_INFO"] = self.path
        env["SERVER_NAME"] = self.server_name
        env["SERVER_PORT"] = str(self.server_port)
        return env

    def start_response(self, status, response_headers, exc_info=None):
        # Add necessary server headers
        server_headers = [
            ("Date", utils.format_datetime(datetime.now())),
            ("Server", "WSGIServer 0.1"),
        ]
        self.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = f"HTTP/1.1 {status}\r\n"
            for header in response_headers:
                response += "{0}: {1}\r\n".format(*header)
            response += "\r\n"
            for data in result:
                response += data.decode("utf-8")
            print("".join(f"> {line}\n" for line in response.splitlines()))
            response_bytes = response.encode()
            self.client_connection.sendall(response_bytes)
        finally:
            self.client_connection.close()


def make_server(server_address, application_):
    server = WSGIServer(server_address)
    server.set_app(application_)
    return server


SERVER_ADDRESS = (HOST, PORT) = "", 8000

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Provide a WSGI application object as module:callable")

    app_path = sys.argv[1]
    module, application = app_path.split(":")

    module = __import__(module)
    application = getattr(module, application)

    httpd = make_server(SERVER_ADDRESS, application)
    print(f"🚀 WSGIServer: Serving HTTP on port {PORT}...\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt as ex:
        print("Server stopped by user.")
