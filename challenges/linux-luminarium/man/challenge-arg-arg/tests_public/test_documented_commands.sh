#!/bin/sh
set -eu

test -r /etc/hostname
/challenge/challenge --printfile /etc/hostname >/dev/null
