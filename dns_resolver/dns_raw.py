import binascii
import ctypes
import socket
import struct


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


def send_udp_message(message_: str, address: str, port: int = 53) -> bytes:
    """
    Sends message to DNS server via UDP.
    :param message_: should be a hexadecimal encoded string
    :param address: DNS server IP
    :param port: DNS server port
    :return: data received from DNS server
    """
    message_ = message_.replace(" ", "").replace("\n", "")
    server_address = (address, port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(binascii.unhexlify(message_), server_address)
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
    if rcode == 0:
        return "No error"
    elif rcode == 1:
        return "Format error (name server could not interpret your request)"
    elif rcode == 2:
        return "Server failure"
    elif rcode == 3:
        return "Name Error (Domain does not exist)"
    elif rcode == 4:
        return "Not implemented (name server does not support your request type)"
    elif rcode == 5:
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
    if qtype == 1:
        return "A"
    elif qtype == 2:
        return "NS"
    elif qtype == 5:
        return "CNAME"
    elif qtype == 15:
        return "MX"
    elif qtype == 28:
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
    if qclass == 1:
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

        if atype == 1:
            aaddr = (
                socket.inet_ntop(
                    socket.AF_INET, raw_bytes[offset + 12 : offset + 12 + 4]
                )
                + " (IPv4)"
            )
            offset += 12 + 4
        elif atype == 28:
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


message = (
    "AA AA 01 00 00 01 00 00 00 00 00 00 "
    "07 65 78 61 6d 70 6c 65 03 63 6f 6d 00 00 01 00 01"
)

if __name__ == "__main__":
    response = send_udp_message(message, "198.41.0.4", 53)
    print_dns_response(response)
