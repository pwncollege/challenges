#!/usr/bin/env python3

import os
from pathlib import Path
import socket
import subprocess

capture = Path("/challenge/traffic.pcap")
assert capture.is_file() and capture.stat().st_size > 24
assert not os.access(capture, os.W_OK)
assert b"pwn.college{" not in capture.read_bytes()
assert not os.access("/challenge/captures", os.R_OK) and not os.access("/challenge/captures", os.X_OK)
# Nothing may serve the flag directly.
with socket.socket() as connection:
    connection.settimeout(1)
    assert connection.connect_ex(("127.0.0.1", 443)) != 0

def fields(display_filter, field):
    return subprocess.check_output(
        ["tshark", "-r", str(capture), "-Y", display_filter, "-T", "fields", "-e", field],
        text=True,
    ).strip()

assert fields("tls.handshake.type == 2", "tls.handshake.version") == "0x0303"
assert fields("tls.handshake.type == 2", "tls.handshake.ciphersuite") == "0x009c"
assert fields("tls.handshake.type == 11", "tls.handshake.certificate")
assert fields("tls.handshake.type == 16", "frame.number")
assert fields("tls.record.content_type == 23", "frame.number")
assert not fields("http", "frame.number")
