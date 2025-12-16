#!/usr/bin/env python3

import subprocess
import time

proc = subprocess.Popen(
    ["/challenge/run.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

output = ""
start = time.time()
while "Decrypted secret?" not in output:
    if time.time() - start > 2:
        raise AssertionError("no prompt")
    line = proc.stdout.readline()
    if not line:
        break
    output += line

assert "The key:" in output
assert "Encrypted secret:" in output
assert "Decrypted secret?" in output

proc.stdin.write("0\n")
proc.stdin.flush()

remaining = proc.communicate(timeout=2)[0]
assert "INCORRECT!" in remaining
