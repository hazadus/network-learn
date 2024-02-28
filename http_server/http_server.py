"""
Very simple HTTP server.

Serves static files, or directory listings.
Built to learn HTTP protocol.
"""

import settings
from serve import serve_forever

if __name__ == "__main__":
    try:
        serve_forever(settings.DEFAULT_HOST, settings.DEFAULT_PORT)
    except KeyboardInterrupt:
        ...
