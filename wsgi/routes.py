"""
Example usage:
    uwsgi --http :8000 --wsgi-file hello.py
    curl -X GET http://127.0.0.1:8000/hello
    curl -X GET http://127.0.0.1:8000/hello/Alexander
"""

import json
import re
from functools import partial
from typing import Callable, Iterable


class WSGIApp:

    def __init__(self):
        self._routes = {}

    def route(self, rule: str) -> Callable:
        def decorator(f: Callable) -> Callable:
            self._routes.update({rule: f})
            return f

        return decorator

    def _get_route_handler(self, path: str) -> Callable | None:
        # Пробуем сначала просто найти подходящий хэндлер
        handler = self._routes.get(path, None)
        if handler:
            return handler

        # Если не нашли сходу, пробуем найти хэндлер с переменной
        for key, handler in self._routes.items():
            # Ищем имя переменной в key
            var_names = re.findall(r"<(.+)>", key)
            if not len(var_names):
                continue

            var_name = var_names[0]

            # Пробуем вытащить значение переменной из path
            pattern = key.replace(f"<{var_name}>", "(.+)")
            matches = re.findall(pattern, path)

            if not len(matches):
                continue

            # Если значение нашлось, значит это нужный нам хэндлер
            match = matches[0]
            kwargs = {var_name: match}
            return partial(handler, **kwargs)

    def __call__(self, environ: dict, start_response: Callable) -> Iterable:
        path = environ["PATH_INFO"]
        handler = self._get_route_handler(path)

        if handler:
            body = handler()
            status = "200 OK"
        else:
            body = ""
            status = "404 Not Found"

        headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ]

        start_response(status, headers)

        return [body.encode()]


application = WSGIApp()


@application.route("/hello")
def handler_hello() -> str:
    return json.dumps({"response": "Hello, world!"}, indent=4)


@application.route("/hello/<name>")
def handler_hello_name(name: str) -> str:
    return json.dumps({"response": f"Hello, {name}!"}, indent=4)
