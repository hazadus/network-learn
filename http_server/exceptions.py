"""
Custom exceptions.
"""


class HTTPError(Exception):
    def __init__(self, status: int, reason: str, body: bytes | None = None):
        super()
        self.status = status
        self.reason = reason
        self.body = body
