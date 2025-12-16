#!/usr/bin/env python3
import subprocess

p = subprocess.Popen(
    ["/challenge/run.py"],
    stdout=subprocess.PIPE,
    text=True,
)
assert "TASK:" in p.stdout.readline()
