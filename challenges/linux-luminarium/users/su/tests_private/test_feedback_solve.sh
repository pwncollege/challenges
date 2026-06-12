#!/bin/bash
set -eo pipefail

printf 'hack-the-planet\n' | su -c '/challenge/run; cat /flag' | tee /dev/stderr | grep -F 'pwn.college{'
