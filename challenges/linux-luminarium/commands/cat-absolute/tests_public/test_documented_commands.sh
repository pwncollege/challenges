#!/bin/sh
set -eu

test -r /etc/hostname
cat /etc/hostname >/dev/null
/challenge/run | grep -Fq "/flag"
