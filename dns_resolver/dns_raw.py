"""
Resolve domain names using DNS messages sent via UPD, without 3rd-party libraries.
"""

import binascii
import ctypes
import random
import socket
import struct
from dataclasses import dataclass
from enum import IntEnum
from io import BytesIO


@dataclass
class DNSHeader:
    """
    Represents DNS message header.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#page-26
    """

    id: int = random.randint(0, 65535)  # 16 bit: message identifier
    qr: int = 0b0  # 1 bit: flag, query 0, response 1
    opcode: int = 0b0000  # 4 bit: kind of query, 0 = standard query
    aa: int = 0b0  # 1 bit: authoritative answer
    tc: int = 0b0  # 1 bit: message truncated flag
    rd: int = 0b1  # 1 bit: recursion desired flag
    ra: int = 0b0  # 1 bit: recursion available flag (may be set in response)
    z: int = 0b000  # 3 bit: reserved for future use, must be zero
    rcode: int = 0b0000  # 4 bit: response code
    qdcount: int = 0b0000000000000001  # 16 bit: number of questions
    ancount: int = 0b0000000000000000  # 16 bit: number of answers
    nscount: int = 0b0000000000000000  # 16 bit: number of authority records
    arcount: int = 0b0000000000000000  # 16 bit: number of additional records

    def as_hex_str(self) -> str:
        params = str(self.qr)
        params += str(self.opcode).zfill(4)
        params += str(self.aa) + str(self.tc) + str(self.rd) + str(self.ra)
        params += str(self.z).zfill(3)
        params += str(self.rcode).zfill(4)

        # Convert `params` "binary in string" to int, then format it as hex number in string:
        params = f"{int(params, base=2):04x}"

        header = ""
        header += f"{self.id:04x}"
        header += params
        header += f"{self.qdcount:04x}"
        header += f"{self.ancount:04x}"
        header += f"{self.nscount:04x}"
        header += f"{self.arcount:04x}"

        return header

    def _rcode_to_str(self) -> str:
        """
        Convert response code to description string.
        Reference: https://datatracker.ietf.org/doc/html/rfc1035#page-27
        :return: RCODE description
        """
        if self.rcode == RCODE.NO_ERROR:
            return "No error"
        elif self.rcode == RCODE.FORMAT_ERROR:
            return "Format error (name server could not interpret your request)"
        elif self.rcode == RCODE.SERVER_FAILURE:
            return "Server failure"
        elif self.rcode == RCODE.NAME_ERROR:
            return "Name Error (Domain does not exist)"
        elif self.rcode == RCODE.NOT_IMPLEMENTED:
            return "Not implemented (name server does not support your request type)"
        elif self.rcode == RCODE.REFUSED:
            return "Refused (name server refused your request for policy reasons)"
        else:
            return "WARNING: Unknown rcode"

    def pretty_print(self):
        print("Message ID: %i" % self.id)
        print("Response code: %s" % self._rcode_to_str())
        print(
            "Counts: Query %i, Answer %i, Authority %i, Additional %i"
            % (self.qdcount, self.ancount, self.nscount, self.arcount)
        )

    @staticmethod
    def from_bytes(reader: BytesIO) -> "DNSHeader":
        """
        Parse header from DNS message and create `DNSHeader` instance.
        """
        header_struct = struct.Struct("!H2sHHHH")
        header_raw = reader.read(header_struct.size)

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
        ) = header_struct.unpack(header_raw)

        # Move raw header bytes to the `bitfields` struct memory location
        # so we can access its members:
        ctypes.memmove(ctypes.addressof(bitfields), bitfields_raw, 2)

        return DNSHeader(
            id=hdr_message_id,
            qr=bitfields.qr,
            opcode=bitfields.opcode,
            aa=bitfields.aa,
            tc=bitfields.tc,
            rd=bitfields.rd,
            ra=bitfields.ra,
            z=bitfields.z,
            rcode=bitfields.rcode,
            qdcount=hdr_qdcount,
            ancount=hdr_ancount,
            nscount=hdr_nscount,
            arcount=hdr_arcount,
        )


class DNSHeaderBitFields(ctypes.BigEndianStructure):
    """
    Represents DNS message header parameters, 16 bit long.
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


@dataclass
class DNSQuestion:
    """
    Represents Question section of the DNS message.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.2
    """

    domain: str
    qtype: QTYPE = QTYPE.A  # 16 bit: type = A records, i.e. "host address"
    qclass: QCLASS = QCLASS.IN  # 16 bit: class = Internet

    def __str__(self):
        return (
            f"DNSQuestion(domain={self.domain}, qtype={self.qtype} ({qtype_to_str(self.qtype)}), "
            f"qclass={self.qclass} ({class_to_str(self.qclass)}))"
        )

    def _encode_domain_name(self) -> str:
        """
        Encode domain name for DNS Question in hex string representation.
        :return: encoded domain name encoded as hex string
        """
        # QNAME a domain name represented as a sequence of labels, where each label consists of
        # a length octet followed by that number of octets. The domain name terminates with the
        # zero length octet for the null label of the root. Note that this field may be an odd
        # number of octets; no padding is used.
        qname = ""
        addr_parts = self.domain.split(".")
        for part in addr_parts:
            addr_len = f"{len(part):02x}"
            addr_part = binascii.hexlify(part.encode())
            qname += addr_len
            qname += addr_part.decode()

        qname += "00"  # Terminating bit for QNAME
        return qname

    def as_hex_str(self) -> str:
        question = self._encode_domain_name()
        question += f"{self.qtype:04x}"  # 16 bit
        question += f"{self.qclass:04x}"  # 16 bit
        return question

    @staticmethod
    def from_bytes(reader: BytesIO) -> "DNSQuestion":
        name = decode_name(reader)
        data = reader.read(4)
        qtype, qclass = struct.unpack("!HH", data)
        return DNSQuestion(domain=name.decode(), qtype=qtype, qclass=qclass)


@dataclass
class DNSRecord:
    """
    Represents DNS resource record.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.3
    """

    name: bytes
    type_: QTYPE
    class_: QCLASS
    ttl: int
    rdata: bytes
    address: str

    def __str__(self):
        return (
            f"DNSRecord(name={self.name}, type_={self.type_} ({qtype_to_str(self.type_)}), "
            f"class_={self.class_} ({class_to_str(self.class_)}), ttl={self.ttl}, rdata={self.rdata}) "
            f"rdlength={len(self.rdata)}, Address: {self.address}"
        )

    @staticmethod
    def from_bytes(reader: BytesIO) -> "DNSRecord":
        name = decode_name(reader)
        # HHIH means: 2-byte type, 2-byte class, 4-byte ttl, 2-byte rdlength = 10 bytes
        # Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.3
        record_struct = struct.Struct("!HHIH")
        data = reader.read(record_struct.size)
        type_, class_, ttl, rdlength = record_struct.unpack(data)

        rdata_pos = reader.tell()
        rdata = reader.read(rdlength)

        # Parse address (IP or domain) from rdata
        if type_ == QTYPE.A:
            address = socket.inet_ntop(socket.AF_INET, rdata)
        elif type_ == QTYPE.AAAA:
            address = socket.inet_ntop(socket.AF_INET6, rdata)
        elif type_ == QTYPE.NS:
            reader.seek(rdata_pos)
            address = decode_name(reader=reader).decode()
        else:
            address = "WARNING: Unknown address format."

        return DNSRecord(name, type_, class_, ttl, rdata, address)


@dataclass
class DNSMessage:
    """
    Represents full DNS message.
    Reference: https://datatracker.ietf.org/doc/html/rfc1035#section-4.1
    """

    header: DNSHeader
    questions: list[DNSQuestion]
    answers: list[DNSRecord]
    authorities: list[DNSRecord]
    additionals: list[DNSRecord]

    @staticmethod
    def from_bytes(reader: BytesIO) -> "DNSMessage":
        header = DNSHeader.from_bytes(reader)
        questions = [DNSQuestion.from_bytes(reader) for _ in range(header.qdcount)]
        answers = [DNSRecord.from_bytes(reader) for _ in range(header.ancount)]
        authorities = [DNSRecord.from_bytes(reader) for _ in range(header.nscount)]
        additionals = [DNSRecord.from_bytes(reader) for _ in range(header.arcount)]
        return DNSMessage(
            header=header,
            questions=questions,
            answers=answers,
            authorities=authorities,
            additionals=additionals,
        )

    def pretty_print(self):
        self.header.pretty_print()
        [print(q) for q in self.questions]
        [print(answ) for answ in self.answers]
        [print(ns) for ns in self.authorities]
        [print(ar) for ar in self.additionals]

    @property
    def nameserver_ip(self) -> str | None:
        for record in self.additionals:
            if record.type_ == QTYPE.A:
                return record.address

    @property
    def nameserver_name(self) -> str | None:
        for record in self.authorities:
            if record.type_ == QTYPE.NS:
                return record.address


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


def decode_name(reader: BytesIO) -> bytes:
    parts = []
    while (length := reader.read(1)[0]) != 0:
        # Check if two upper bits are set - it means we have to "decompress" the name:
        if length & 0b1100_0000:
            parts.append(decode_compressed_name(length, reader))
            break
        else:
            parts.append(reader.read(length))
    return b".".join(parts)


def decode_compressed_name(length, reader):
    """
    Reference : https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.4
    :param length:
    :param reader:
    :return:
    """
    # Get bottom 6 bits and the following byte, and convert the two bytes to int
    pointer_bytes = bytes([length & 0b0011_1111]) + reader.read(1)
    pointer = struct.unpack("!H", pointer_bytes)[0]
    # Save position, seek to position decoded above, read name, restore position:
    current_pos = reader.tell()
    reader.seek(pointer)
    result = decode_name(reader)
    reader.seek(current_pos)
    return result


def create_dns_message(domain: str) -> bytes:
    """
    Compile DNS message ready to send via UDP.
    :param domain: domain name we want to look up
    :return: DNS message
    """
    header = DNSHeader(rd=0)  # No recursion
    question = DNSQuestion(domain=domain)

    message = header.as_hex_str()
    message += question.as_hex_str()

    # Convert string hex representation into real bytes
    return binascii.unhexlify(message)


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


def resolve(domain: str) -> str:
    """
    Resolve domain name.
    :param domain: domain name to resolve
    :return: IP address of the `domain`
    """
    # Root server IP (list of all root servers - https://www.iana.org/domains/root/servers):
    nameserver = "198.41.0.4"
    while True:
        print(f"Querying {nameserver} for {domain}")
        msg = create_dns_message(domain)
        response = send_udp_message(msg, nameserver)
        received_msg = DNSMessage.from_bytes(reader=BytesIO(response))

        if len(received_msg.answers):
            return received_msg.answers[0].address
        elif received_msg.nameserver_ip:
            nameserver = received_msg.nameserver_ip
        elif received_msg.nameserver_name:
            nameserver = resolve(received_msg.nameserver_name)
        else:
            raise Exception(f"Can't resolve {domain}!")


if __name__ == "__main__":
    domains = [
        "hazadus.ru",
        "rss.hazadus.ru",
        "github.com",
        "python.org",
        "twitter.com",
    ]
    [print(f"{domain} IP is", resolve(domain), "\n") for domain in domains]
