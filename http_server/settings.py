"""
All settings of HTTP Server are here.
"""

import os
import platform

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
STATIC_ROOT = "./static"
STATIC_DIR = os.path.abspath(STATIC_ROOT)
SERVER_TITLE = f"Hazardous HTTP Server (Python v.{platform.python_version()})"
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
EXTENSION_TO_MIME_TYPE = {
    ".htm": "text/html; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".png": "image/png",
    ".bin": "application/octet-stream",
    ".css": "text/css",
    ".csv": "text/csv",
    ".eot": "application/vnd.ms-fontobject",
    ".gif": "image/gif",
    ".ico": "image/vnd.microsoft.icon",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".js": "text/javascript",
    ".json": "application/json",
    ".mjs": "text/javascript",
    ".m4a": "audio/m4a",
    ".mp3": "audio/mpeg",
    ".m4v": "video/mp4",
    ".mp4": "video/mp4",
    ".otf": "font/otf",
    ".pdf": "application/pdf",
    ".svg": "image/svg+xml",
    ".tar": "application/x-tar",
    ".txt": "text/plain",
    ".ttf": "font/ttf",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".zip": "application/zip",
}
DEFAULT_CONTENT_TYPE = "application/octet-stream"
