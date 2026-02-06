#!/bin/sh
set -eu

mkdir -p /run/workshop/tinkering /run/workshop/assembled
chmod 0711 /run/workshop /run/workshop/tinkering
chmod 0733 /run/workshop/assembled

/challenge/workshop.py &
