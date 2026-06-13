#!/bin/bash
set -eo pipefail

printf '%s\n' /challenge/pwn /challenge/college > /tmp/solve.sh
echo feedback-test-secret > /tmp/.pwn-secret

BASH_ENV=/challenge/.hook bash /tmp/solve.sh | /challenge/solve | tee /dev/stderr | grep -F 'pwn.college{'
