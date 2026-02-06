#!/usr/bin/exec-suid -- /bin/bash -p

set -euo pipefail

PATH="/runtime/qemu/bin:$PATH"

qemu-system-x86_64 \
  -machine q35 \
  -cpu qemu64 \
  -m 512M \
  -nographic \
  -no-reboot \
  -kernel /runtime/out/bzImage \
  -initrd /runtime/out/rootfs.cpio.gz \
  -append "console=ttyS0 quiet panic=-1" \
  -device pypu-pci \
  -serial stdio \
  -monitor none
