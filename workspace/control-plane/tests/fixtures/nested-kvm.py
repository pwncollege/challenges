"""Execute a tiny guest through the workspace's /dev/kvm, including KVM_RUN."""

import ctypes
import fcntl
import mmap
import os
import signal
import struct


signal.alarm(10)
kvm = os.open("/dev/kvm", os.O_RDWR | os.O_CLOEXEC)
assert fcntl.ioctl(kvm, 0xAE00) == 12  # KVM_GET_API_VERSION
vm = fcntl.ioctl(kvm, 0xAE01, 0)  # KVM_CREATE_VM
memory = mmap.mmap(-1, 4096)
address = ctypes.addressof(ctypes.c_char.from_buffer(memory))
fcntl.ioctl(vm, 0x4020AE46, struct.pack("IIQQQ", 0, 0, 0, 4096, address))
# 16-bit guest: mov al, 42; out 0xe9, al; hlt.
memory[:5] = bytes.fromhex("b02ae6e9f4")
vcpu = fcntl.ioctl(vm, 0xAE41, 0)  # KVM_CREATE_VCPU
run = mmap.mmap(vcpu, fcntl.ioctl(kvm, 0xAE04), flags=mmap.MAP_SHARED)
sregs = bytearray(312)
fcntl.ioctl(vcpu, 0x8138AE83, sregs)  # KVM_GET_SREGS
struct.pack_into("Q", sregs, 0, 0)  # CS base
struct.pack_into("H", sregs, 12, 0)  # CS selector
fcntl.ioctl(vcpu, 0x4138AE84, sregs)  # KVM_SET_SREGS
fcntl.ioctl(vcpu, 0x4090AE82, struct.pack("18Q", *([0] * 17), 2))  # KVM_SET_REGS
fcntl.ioctl(vcpu, 0xAE80, 0)  # KVM_RUN
assert struct.unpack_from("I", run, 8)[0] == 2  # KVM_EXIT_IO
direction, size, port, count, offset = struct.unpack_from("BBHIQ", run, 32)
assert (direction, size, port, count, run[offset]) == (1, 1, 0xE9, 1, 42)
fcntl.ioctl(vcpu, 0xAE80, 0)
assert struct.unpack_from("I", run, 8)[0] == 5  # KVM_EXIT_HLT
print("nested KVM executed guest instructions")
