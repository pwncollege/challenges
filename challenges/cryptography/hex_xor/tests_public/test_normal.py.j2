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

assert "Encrypted secret:" in output
assert "0x" in output

proc.stdin.write("zz\n")
proc.stdin.flush()

remaining = proc.communicate(timeout=2)[0]
assert "INCORRECT!" in remaining or proc.returncode != 0
