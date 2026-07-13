#!/bin/sh
set -eu

workdir="$(mktemp -d)"
cd "$workdir"
echo hi > asdf
[ "$(cat asdf)" = "hi" ]
/challenge/run | grep -Fq "PWN"
