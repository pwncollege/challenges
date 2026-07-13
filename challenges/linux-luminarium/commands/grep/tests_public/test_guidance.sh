#!/bin/sh
set -eu

test -r /challenge/data.txt
grep -F "pwn.college" /challenge/data.txt >/dev/null
/challenge/run | grep -Fq "/challenge/data.txt"
