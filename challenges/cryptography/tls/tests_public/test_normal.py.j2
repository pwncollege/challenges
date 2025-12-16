#!/usr/bin/env python3

import subprocess
import time

proc = subprocess.Popen(
    ["/challenge/crypto.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

output = ""
start = time.time()
while "root certificate (b64)" not in output:
    if time.time() - start > 2:
        raise AssertionError("no root certificate")
    line = proc.stdout.readline()
    if not line:
        break
    output += line

assert "root key d:" in output
assert "root certificate (b64)" in output
assert "root certificate signature (b64)" in output

proc.stdin.write("AAAA\n")
proc.stdin.write("AAAA\n")
proc.stdin.flush()

proc.communicate(timeout=2)
