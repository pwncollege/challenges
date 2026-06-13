#!/bin/bash
set -eo pipefail

OUTPUT=$(printf 'hack-the-planet\n' | su -c '/challenge/run; cat /flag')
printf '%s\n' "$OUTPUT" | tee /dev/stderr

grep -F 'Congratulations, you have become root!' <<< "$OUTPUT"
grep -F 'pwn.college{' <<< "$OUTPUT"
! grep -F 'DESCRIPTION.md' <<< "$OUTPUT"
