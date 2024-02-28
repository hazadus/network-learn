"""
All settings of HTTP Server are here.
"""

import os

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
