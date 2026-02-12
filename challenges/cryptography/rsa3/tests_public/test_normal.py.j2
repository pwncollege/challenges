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
while "challenge:" not in output:
    if time.time() - start > 2:
        raise AssertionError("no challenge printed")
    line = proc.stdout.readline()
    if not line:
        break
    output += line

assert "e:" in output
assert "d:" in output
assert "n:" in output
assert "challenge:" in output

proc.stdin.write("0\n")
proc.stdin.flush()

proc.communicate(timeout=2)
