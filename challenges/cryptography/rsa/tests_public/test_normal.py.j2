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

assert "(public)  n =" in output
assert "(public)  e =" in output
assert "(private) d =" in output
assert "Flag Ciphertext (hex):" in output
