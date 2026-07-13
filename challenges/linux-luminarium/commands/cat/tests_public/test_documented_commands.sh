#!/bin/sh
set -eu

test -r /etc/hostname
cat /etc/hostname >/dev/null
[ ! -r /flag ]

workdir="$(mktemp -d)"
cd "$workdir"
printf 'This is my file!\n' > myfile
printf 'This is your file!\n' > yourfile

[ "$(cat myfile)" = "This is my file!" ]
[ "$(cat yourfile)" = "This is your file!" ]
[ "$(cat myfile yourfile)" = "This is my file!
This is your file!" ]
[ "$(cat myfile yourfile myfile)" = "This is my file!
This is your file!
This is my file!" ]

/challenge/run | grep -Fq "home directory"
