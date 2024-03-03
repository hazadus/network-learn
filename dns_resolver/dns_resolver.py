"""
DNS resolver (using dnspython library).
"""

import dns.message
import dns.query
import dns.rdatatype


def resolve(domain: str):
    root_nameserver = "198.41.0.4"

    nameserver = root_nameserver
    while True:
        reply = query(domain, nameserver)

        ip = get_answer(reply)

        if ip:
            # We got IP right away:
            print(f"resolve {ip=}")
            return ip

        next_nameserver = get_glue(reply)
        if next_nameserver:
            # We got "glue record" with IP of the next nameserver to query
            print(f"resolve {next_nameserver=}")
            nameserver = next_nameserver
        else:
            # We got domain name of the next nameserver to query
            nameserver_domain = get_nameserver(reply)
            print(f"resolve {nameserver_domain=}")
            nameserver = resolve(nameserver_domain)


def query(name: str, nameserver: str) -> dns.message.Message:
    dns_query = dns.message.make_query(name, "A")
    return dns.query.udp(dns_query, nameserver)


def get_answer(reply: dns.message.Message) -> str | None:
    """Try to get domain IP from the DNS message.
    :param reply: message received from nameserver
    :return: IP or None
    """
    for record in reply.answer:
        print(f"get_answer {record=}")
        if record.rdtype == dns.rdatatype.A:
            return record[0].address


def get_glue(reply: dns.message.Message) -> str | None:
    """Try to get IP of the next nameserver to query from the DNS message.

    The root nameserver can return two kinds of DNS records:

    - NS records (in the Authority section);
    - glue records (in the Additional section) with nameserver IP.

    Glue records help resolvers to avoid infinite loops.

    :param reply: message received from nameserver
    :return: IP or None
    """
    for record in reply.additional:
        print(f"get_glue {record=}")
        if record.rdtype == dns.rdatatype.A:
            return record[0].address


def get_nameserver(reply: dns.message.Message) -> str | None:
    """Try to get domain name of the next nameserver to query from the DNS message.
    :param reply: message received from nameserver
    :return: domain name or None
    """
    for record in reply.authority:
        print(f"get_nameserver {record=}")
        if record.rdtype == dns.rdatatype.NS:
            return record[0].target


if __name__ == "__main__":
    ip_ = resolve("rss.hazadus.ru")
    print(f"{ip_=}")
