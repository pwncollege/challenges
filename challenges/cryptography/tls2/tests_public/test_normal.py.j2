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
while "A:" not in output:
    if time.time() - start > 3:
        raise AssertionError("no DH parameters")
    line = proc.stdout.readline()
    if not line:
        break
    output += line

assert "p:" in output
assert "g:" in output
assert "A:" in output

proc.stdin.write("1\n")
proc.stdin.flush()

proc.communicate(timeout=2)
