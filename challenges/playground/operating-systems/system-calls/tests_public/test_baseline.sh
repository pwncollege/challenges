#!/bin/bash
set -euo pipefail

test "$(id -u)" = 1000
test -w /usr/src/linux/kernel/sys.c
test -w /var/cache/ccache
test -L /boot/vmlinuz
test "$(readlink /boot/vmlinuz)" = /usr/src/linux/arch/x86/boot/bzImage
test ! -w /boot/initramfs.cpio.gz
test ! -r /flag

test "$(git -C /usr/src/linux diff --name-only)" = \
    $'arch/x86/entry/syscalls/syscall_64.tbl\ninclude/linux/syscalls.h\nkernel/sys.c'
if output=$(/challenge/run 2>&1); then
    printf '%s\n' "$output"
    echo 'The syscall stub should not pass.' >&2
    exit 1
fi
printf '%s\n' "$output"
grep -Fq 'The hello syscall is not implemented.' <<< "$output"
