#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"

gcc -shared -fPIC -o crash_to_flag.so crash_to_flag.c
gcc -o test_crash_to_flag test_crash_to_flag.c
if LD_PRELOAD=$PWD/crash_to_flag.so ./test_crash_to_flag | tee /dev/stderr | grep -q pwn.college
then
	echo "Success!"
else
	echo "FAIL!"
	exit 1
fi
