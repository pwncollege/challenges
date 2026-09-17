#!/bin/bash
set -euo pipefail

test "$(id -u)" = 1000
test -w /usr/src/linux/kernel/sys.c
test -w /var/cache/ccache
test "$(readlink /boot/vmlinuz)" = /usr/src/linux/arch/x86/boot/bzImage
test ! -w /usr/src/initramfs/init
test ! -w /usr/src/initramfs/usr/bin/test-memory
test ! -r /flag
git -C /usr/src/linux diff --exit-code

test -L /challenge/checkpoint.h
test "$(readlink /challenge/checkpoint.h)" = /usr/local/include/checkpoint.h
test -r /challenge/checkpoint.h
test ! -w /challenge/checkpoint.h
test -L /challenge/tests
test ! -w /challenge/tests
for name in variables memory files descriptors duplicates process signals credentials lifecycle game; do
    test -r "/challenge/tests/$name.c"
    test ! -w "/challenge/tests/$name.c"
done

if output=$(/challenge/run 2>&1); then
    printf '%s\n' "$output"
    echo 'The unmodified kernel should not pass.' >&2
    exit 1
fi
printf '%s\n' "$output"
for name in variables memory files descriptors duplicates process signals credentials lifecycle game; do
    grep -Fq "Failed: $name" <<< "$output"
done
! grep -Fq 'Checkpoint tests passed.' <<< "$output"
! grep -Fq 'Correct!' <<< "$output"
