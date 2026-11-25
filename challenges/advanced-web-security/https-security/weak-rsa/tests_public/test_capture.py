#!/usr/bin/env python3

import os
from pathlib import Path
import socket

capture = Path("/challenge/traffic.pcap")
assert capture.is_file() and capture.stat().st_size > 24
assert not os.access(capture, os.W_OK)
data = capture.read_bytes()
assert b"pwn.college{" not in data and b"HTTP/1.1" not in data
assert not os.access("/challenge/captures", os.R_OK) and not os.access("/challenge/captures", os.X_OK)
# Nothing may serve the flag directly.
with socket.socket() as connection:
    connection.settimeout(1)
    assert connection.connect_ex(("127.0.0.1", 443)) != 0

# Reassemble the server's side of the captured connection and check its TLS records.
assert data[:4] == bytes.fromhex("d4c3b2a1") and int.from_bytes(data[20:24], "little") == 1  # Ethernet
segments = {}
offset = 24
while offset < len(data):
    length = int.from_bytes(data[offset + 8 : offset + 12], "little")
    ip = data[offset + 30 : offset + 16 + length]
    offset += 16 + length
    tcp = ip[(ip[0] & 15) * 4 : int.from_bytes(ip[2:4], "big")]
    if int.from_bytes(tcp[0:2], "big") == 443 and (payload := tcp[(tcp[12] >> 4) * 4 :]):
        segments[int.from_bytes(tcp[4:8], "big")] = payload
first = next(iter(segments))
stream = b"".join(segments[seq] for seq in sorted(segments, key=lambda seq: (seq - first) % 2**32))

content_types, handshake = [], b""
while stream:
    length = int.from_bytes(stream[3:5], "big")
    content_types.append(stream[0])
    if stream[0] == 22 and 20 not in content_types:
        handshake += stream[5 : 5 + length]
    stream = stream[5 + length :]
assert 20 in content_types and 23 in content_types  # ChangeCipherSpec, then encrypted application data

messages = {}
while handshake:
    length = int.from_bytes(handshake[1:4], "big")
    messages[handshake[0]] = handshake[4 : 4 + length]
    handshake = handshake[4 + length :]
server_hello = messages[2]
assert server_hello[:2] == b"\x03\x03"  # TLS 1.2
cipher_suite = server_hello[35 + server_hello[34] : 37 + server_hello[34]]
assert cipher_suite == b"\x00\x9c"  # TLS_RSA_WITH_AES_128_GCM_SHA256: RSA key exchange
assert 11 in messages and 12 not in messages  # a Certificate, and no ServerKeyExchange
