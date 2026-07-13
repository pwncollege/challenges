#!/bin/sh
set -eu

flag_directory="$(cat /tmp/.flag-path)"
output="$(
    cd /home/hacker
    printf '%s\n' 'cd /tmp' 'pwd' 'exit' |
        HOME=/home/hacker HISTFILE=/dev/null \
        /usr/bin/script -qfec \
        '/bin/bash --noprofile --rcfile /challenge/.bashrc -i' /dev/null
)"
printf '%s\n' "$output"
printf '%s\n' "$output" | grep -Fq 'You cannot use the'
printf '%s\n' "$output" | grep -Fq "You used 'cd'!"
printf '%s\n' "$output" | grep -Fq "$flag_directory/flag"
printf '%s\n' "$output" | grep -Fq '/home/hacker'
