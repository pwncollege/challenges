#!/usr/bin/exec-suid -- /bin/bash -p

set -euo pipefail
umask 077

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <list>" >&2
    exit 1
fi

LIST_SRC="$1"
if [ ! -d "$LIST_SRC" ]; then
    echo "error: list must be a directory" >&2
    exit 1
fi

LOG_FILE="$(mktemp)"
cleanup() { rm -f "$LOG_FILE"; }
trap cleanup EXIT

if ! qemu-system-x86_64 \
    -machine accel=tcg \
    -cpu max \
    -m 512M \
    -nographic \
    -no-reboot \
    -kernel /boot/vmlinuz \
    -initrd /boot/initramfs.cpio.gz \
    -append "console=ttyS0 quiet panic=-1 rdinit=/init" \
    -fsdev local,id=list_fs,path="$LIST_SRC",security_model=none \
    -device virtio-9p-pci,fsdev=list_fs,mount_tag=list \
    -serial stdio \
    -monitor none | tee "$LOG_FILE"; then
    echo "error: VM execution failed" >&2
    exit 1
fi

if grep -q "NAUGHTY" "$LOG_FILE"; then
    exit 1
fi

if ! grep -q "NICE" "$LOG_FILE"; then
    exit 1
fi

cat /flag
