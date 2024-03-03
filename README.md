# 🕸️🖥️ network-learn

В этом репозитории на практике изучаю работу с сетью.

## `socket` module

Разбираемся с работой сокетов на простейших примерах.

- Простейший эхосервер: [sockets/echo_server.py](sockets/echo_server.py)
- Клиент для эхосервера: [sockets/basic_client.py](sockets/basic_client.py)

## HTTP

Изучаем работу протокола HTTP на практике.

- Простой HTTP-сервер с синхронной обработкой запросов: [http_server/http_server.py](http_server/http_server.py)

## DNS

Изучаем работу DNS.

- DNS resolver (используем библиотеку `dnspython`): [dns_resolver/dns_resolver.py](dns_resolver/dns_resolver.py)

## References

- [`socket` — Low-level networking interface](https://docs.python.org/3/library/socket.html)
- [Introducing The Sockets API](https://beej.us/guide/bgnet0/html/split/introducing-the-sockets-api.html#introducing-the-sockets-api)
- [Beej’s Guide to Network Programming](https://beej.us/guide/bgnet) – optional, for C devs.
- [Socket Programming HOWTO](https://docs.python.org/3.12/howto/sockets.html) in Python 3.12 documentation.
