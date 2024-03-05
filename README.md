# 🕸️🖥️ network-learn

В этом репозитории на практике изучаю работу с сетью.

----

## `socket` module

Разбираемся с работой сокетов на простейших примерах.

- Простейший эхосервер: [sockets/echo_server.py](sockets/echo_server.py)
- Клиент для эхосервера: [sockets/basic_client.py](sockets/basic_client.py)

### References

- [`socket` — Low-level networking interface](https://docs.python.org/3/library/socket.html)
- [Introducing The Sockets API](https://beej.us/guide/bgnet0/html/split/introducing-the-sockets-api.html#introducing-the-sockets-api)
- [Beej’s Guide to Network Programming](https://beej.us/guide/bgnet) – optional, for C devs.
- [Socket Programming HOWTO](https://docs.python.org/3.12/howto/sockets.html) in Python 3.12 documentation.

----

## HTTP

Изучаем работу протокола HTTP на практике.

- Простой HTTP-сервер с синхронной обработкой запросов: [http_server/http_server.py](http_server/http_server.py)

----

## DNS

Изучаем работу DNS.

- DNS resolver (используем библиотеку `dnspython`): [dns_resolver/dns_resolver.py](dns_resolver/dns_resolver.py)
- Отправляем запросы к DNS серверу по UDP вручную и печатаем ответ: [dns_resolver/dns_raw.py](dns_resolver/dns_raw.py)

### References

- [Let's hand write DNS messages](https://web.archive.org/web/20180919041301/https://routley.io/tech/2017/12/28/hand-writing-dns-messages.html)
- [RFC 1035: 4.1.1. Header section format](https://datatracker.ietf.org/doc/html/rfc1035#page-26)
- [Lab 8: Network Socket Programming (Intermediate)](https://ecs-network.serv.pacific.edu/ecpe-170/lab/lab-network-inter)
- [`struct`: Byte Order, Size, and Alignment](https://docs.python.org/3.12/library/struct.html#byte-order-size-and-alignment)
- [`struct`: Format Characters](https://docs.python.org/3.12/library/struct.html#format-characters)
- [`ctypes`: `BigEndianStructure`](https://docs.python.org/3.12/library/ctypes.html#ctypes.BigEndianStructure)