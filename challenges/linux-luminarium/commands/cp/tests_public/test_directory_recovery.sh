#!/bin/sh
set -eu

rm -rf /tmp/hack-the-planet
mkdir /tmp/hack-the-planet

output="$(PATH="/challenge/bin:$PATH" cp /flag /tmp/hack-the-planet 2>&1 || true)"
printf '%s\n' "$output"
printf '%s\n' "$output" | grep -Fq '/tmp/hack-the-planet is currently a directory'
printf '%s\n' "$output" | grep -Fq 'rm -r'
test ! -e /tmp/hack-the-planet/flag
