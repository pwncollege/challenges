#!/bin/sh
set -eu

ls -l /usr/bin/sudo >/dev/null
/challenge/run | grep -Fq "/challenge/getroot"
