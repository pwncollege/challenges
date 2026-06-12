#!/bin/bash -e

printf 'hack-the-planet\n' | su -c /challenge/run | tee /dev/stderr | grep -F 'pwn.college{'
