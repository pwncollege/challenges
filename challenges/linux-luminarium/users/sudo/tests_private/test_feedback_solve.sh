#!/bin/bash
set -eo pipefail

{
	sudo /challenge/run
	sudo cat /flag
} | tee /dev/stderr | grep -F 'pwn.college{'
