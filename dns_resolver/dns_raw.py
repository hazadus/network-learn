import binascii
import ctypes
import socket
import struct
from enum import IntEnum


class DNSHeaderBitFields(ctypes.BigEndianStructure):
    """
    Represents DNS message header, 16 bit long.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#page-26
    """

    _fields_ = [
        ("qr", ctypes.c_uint16, 1),
        ("opcode", ctypes.c_uint16, 4),
        ("aa", ctypes.c_uint16, 1),
        ("tc", ctypes.c_uint16, 1),
        ("rd", ctypes.c_uint16, 1),
        ("ra", ctypes.c_uint16, 1),
        ("z", ctypes.c_uint16, 3),
        ("rcode", ctypes.c_uint16, 4),
    ]


class RCODE(IntEnum):
    """
    Represents possible RCODE values.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#page-27
    """

    NO_ERROR = 0
    FORMAT_ERROR = 1
    SERVER_FAILURE = 2
    NAME_ERROR = 3
    NOT_IMPLEMENTED = 4
    REFUSED = 5


class QTYPE(IntEnum):
    """
    Represents possible QTYPE values.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.2
    """

    A = 1  # a host address
    NS = 2  # an authoritative name server
    CNAME = 5  # the canonical name for an alias
    MX = 15  # mail exchange
    AAAA = 28  # IPv6 host address


class QCLASS(IntEnum):
    """
    Represents possible QCLASS values.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.4
    """

    IN = 1


def send_udp_message(message: bytes, address: str, port: int = 53) -> bytes:
    """
    Sends message to DNS server via UDP.
    :param message: actual bytes to send
    :param address: DNS server IP
    :param port: DNS server port
    :return: data received from DNS server
    """
    server_address = (address, port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(message, server_address)
        data, _ = sock.recvfrom(4096)
    finally:
        sock.close()

    return data


def rcode_to_str(rcode: int) -> str:
    """
    Convert response code to description string.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#page-27
    :param rcode: response code
    :return: RCODE description
    """
    if rcode == RCODE.NO_ERROR:
        return "No error"
    elif rcode == RCODE.FORMAT_ERROR:
        return "Format error (name server could not interpret your request)"
    elif rcode == RCODE.SERVER_FAILURE:
        return "Server failure"
    elif rcode == RCODE.NAME_ERROR:
        return "Name Error (Domain does not exist)"
    elif rcode == RCODE.NOT_IMPLEMENTED:
        return "Not implemented (name server does not support your request type)"
    elif rcode == RCODE.REFUSED:
        return "Refused (name server refused your request for policy reasons)"
    else:
        return "WARNING: Unknown rcode"


def qtype_to_str(qtype: int) -> str:
    """
    Convert query type to description string.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.2
    :param qtype: query type code
    :return: QTYPE description
    """
    if qtype == QTYPE.A:
        return "A"
    elif qtype == QTYPE.NS:
        return "NS"
    elif qtype == QTYPE.CNAME:
        return "CNAME"
    elif qtype == QTYPE.MX:
        return "MX"
    elif qtype == QTYPE.AAAA:
        return "AAAA"
    else:
        return "WARNING: Record type not decoded"


def class_to_str(qclass: int) -> str:
    """
    Convert query class to string.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.4
    :param qclass: QCLASS code
    :return: QCLASS description
    """
    if qclass == QCLASS.IN:
        return "IN"
    else:
        return "WARNING: Class not decoded"


def print_dns_response(raw_bytes: bytes) -> None:
    print("Server Response")
    print("---------------")

    # Print out the message header
    bitfields = DNSHeaderBitFields()
    bitfields_raw = bytearray()
    # Unpack format "!H2sHHHH" will spread 12 raw_bytes to the following variables:
    (
        hdr_message_id,  # int, 2 b
        bitfields_raw,  # bytes, 2 b
        hdr_qdcount,  # int, 2 b
        hdr_ancount,  # int, 2 b
        hdr_nscount,  # int, 2 b
        hdr_arcount,  # int, 2 b
    ) = struct.unpack("!H2sHHHH", raw_bytes[0:12])

    # Move raw header bytes to the `bitfields` struct memory location
    # so we can access its members:
    ctypes.memmove(ctypes.addressof(bitfields), bitfields_raw, 2)

    print("Message ID: %i" % hdr_message_id)
    print("Response code: %s" % rcode_to_str(bitfields.rcode))
    print(
        "Counts: Query %i, Answer %i, Authority %i, Additional %i"
        % (hdr_qdcount, hdr_ancount, hdr_nscount, hdr_arcount)
    )

    # Print out each question header
    offset = 12
    for x in range(0, hdr_qdcount):
        qname = ""
        start = True
        while True:
            # "B" is for unsigned char, integer, 1 byte:
            qname_len = struct.unpack("B", raw_bytes[offset : offset + 1])[0]
            if qname_len == 0:
                offset += 1
                break  # Finished parsing out qname
            elif not start:
                qname += "."
            qname += raw_bytes[offset + 1 : offset + 1 + qname_len].decode()
            offset += 1 + qname_len
            start = False

        # Unpack 2 bytes to each variable:
        (qtype, qclass) = struct.unpack("!HH", raw_bytes[offset : offset + 4])

        print("Question %i:" % (x + 1))
        print("  Name: %s" % qname)
        print("  Type: %s" % qtype_to_str(qtype))
        print("  Class: %s" % class_to_str(qclass))

        offset += 4

    # Print out each answer header
    for x in range(0, hdr_ancount):
        (aname, atype, aclass, attl, ardlength) = struct.unpack(
            "!HHHIH", raw_bytes[offset : offset + 12]
        )

        if atype == QTYPE.A:
            aaddr = (
                socket.inet_ntop(
                    socket.AF_INET, raw_bytes[offset + 12 : offset + 12 + 4]
                )
                + " (IPv4)"
            )
            offset += 12 + 4
        elif atype == QTYPE.AAAA:
            aaddr = (
                socket.inet_ntop(
                    socket.AF_INET6, raw_bytes[offset + 12 : offset + 12 + 16]
                )
                + " (IPv6)"
            )
            offset += 12 + 16
        else:
            aaddr = "WARNING: Addr format not IPv4 or IPv6"

        print("Answer %i:" % (x + 1))
        print("  Name: 0x%x" % aname)
        print(
            "  Type: %s, Class: %s, TTL: %i"
            % (qtype_to_str(atype), class_to_str(aclass), attl)
        )
        print("  RDLength: %i bytes" % ardlength)
        print("  Addr: %s" % aaddr)

        # TODO: decode Authority
        # TODO: decode Additional


def create_dns_message(domain: str) -> bytes:
    """
    Compile DNS message ready to send via UDP.
    :param domain: domain name we want to look up
    :return: DNS message
    """
    id_ = 0xAAAA  # 16 bit: message identifier

    # Message parameters
    qr = 0b0  # 1 bit: flag, query 0, response 1
    opcode = 0b0000 # 4 bit: kind of query, 0 = standard query
    aa = 0b0  # 1 bit: authoritative answer
    tc = 0b0  # 1 bit: message truncated flag
    rd = 0b1  # 1 bit: recursion desired flag
    ra = 0b0  # 1 bit: recursion available flag (may be set in response)
    z = 0b000  # 3 bit: reserved for future use, must be zero
    rcode = 0b0000 # 4 bit: response code

    params = str(qr)
    params += str(opcode).zfill(4)
    params += str(aa) + str(tc) + str(rd) + str(ra)
    params += str(z).zfill(3)
    params += str(rcode).zfill(4)

    # Convert `params` "binary in string" to int, then format it as hex number in string:
    params = f"{int(params, base=2):04x}"

    qdcount = 0b0000000000000001  # 16 bit: number of questions
    ancount = 0b0000000000000000  # 16 bit: number of answers
    nscount = 0b0000000000000000  # 16 bit: number of authority records
    arcount = 0b0000000000000000  # 16 bit: number of additional records

    message = ""
    message += f"{id_:04x}"
    message += params
    message += f"{qdcount:04x}"
    message += f"{ancount:04x}"
    message += f"{nscount:04x}"
    message += f"{arcount:04x}"

    # QNAME a domain name represented as a sequence of labels, where each label consists of
    # a length octet followed by that number of octets. The domain name terminates with the
    # zero length octet for the null label of the root. Note that this field may be an odd
    # number of octets; no padding is used.
    addr_parts = domain.split(".")
    for part in addr_parts:
        addr_len = f"{len(part):02x}"
        addr_part = binascii.hexlify(part.encode())
        message += addr_len
        message += addr_part.decode()

    message += "00" # Terminating bit for QNAME

    # QTYPE - Type of the query
    qtype = QTYPE.A  # 16 bit: type = A records, i.e. "host address"
    message += f"{qtype:04x}"

    # QCLASS - Class of the query
    qclass = QCLASS.IN  # 16 bit: class = Internet
    message += f"{qclass:04x}"

    # Convert string hex representation into real bytes
    return binascii.unhexlify(message)


if __name__ == "__main__":
    msg = create_dns_message("rss.hazadus.ru")
    response = send_udp_message(msg, "198.41.0.4")
    print_dns_response(response)

    response = send_udp_message(msg, "8.8.8.8")
    print_dns_response(response)
