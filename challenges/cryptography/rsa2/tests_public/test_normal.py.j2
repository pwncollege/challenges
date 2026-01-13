#!/usr/bin/env python3

import subprocess
import time

proc = subprocess.Popen(
    ["/challenge/run.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

output = ""
start = time.time()
while "Flag Ciphertext" not in output:
    if time.time() - start > 2:
        raise AssertionError("no ciphertext output")
    line = proc.stdout.readline()
    if not line:
        break
    output += line

assert "e =" in output
assert "p =" in output
assert "q =" in output
assert "Flag Ciphertext (hex):" in output
