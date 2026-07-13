#!/bin/sh
set -eu

flag_directory="$(cat /tmp/.flag-path)"
test -r "$flag_directory/flag"
/challenge/run | grep -Fq "$flag_directory/flag"
