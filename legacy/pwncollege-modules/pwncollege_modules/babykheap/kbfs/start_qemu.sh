#!/bin/bash

qemu-system-x86_64 \
	-snapshot \
	-initrd ./rootfs.cpio \
	-kernel ./bzImage \
	-append "console=ttyS0 earlyprintk=serial panic=1000 oops=panic panic_on_warn=1 selinux=0 kaslr" \
	-nographic \
	-m 2G \
	-monitor none \
	-smp 1 \
	-cpu qemu64,smep,smap
