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

output = proc.stdout.readline()
assert "flag_hash" in output

proc.stdin.write("00\n")
proc.stdin.flush()

remaining = proc.communicate(timeout=2)[0]
assert "Collided!" not in remaining
