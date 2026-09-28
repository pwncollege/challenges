"""The shared runtime must be EROFS on a genuinely read-only virtual disk."""

import os
from pathlib import Path


mount = next(
    line.split()
    for line in Path("/proc/mounts").read_text().splitlines()
    if line.split()[1] == "/nix/store"
)
assert mount[2] == "erofs", mount
assert "ro" in mount[3].split(","), mount
device = os.stat("/nix/store").st_dev
read_only = Path(f"/sys/dev/block/{os.major(device)}:{os.minor(device)}/ro")
assert read_only.read_text().strip() == "1"
print("runtime: EROFS mounted from a read-only virtual disk")

root = os.statvfs("/")
assert root.f_blocks * root.f_frsize == 1 << 30, root
root_mount = next(
    line.split()
    for line in Path("/proc/mounts").read_text().splitlines()
    if line.split()[1] == "/"
)
assert root_mount[2] == "overlay", root_mount

temporary = next(
    line.split()
    for line in Path("/proc/mounts").read_text().splitlines()
    if line.split()[1] == "/tmp"
)
assert temporary[2] == "tmpfs", temporary
assert {"nosuid", "nodev"} <= set(temporary[3].split(",")), temporary
assert "noexec" not in temporary[3].split(","), temporary
assert os.stat("/tmp").st_mode & 0o7777 == 0o1777
tmp = os.statvfs("/tmp")
assert tmp.f_blocks * tmp.f_frsize == 1 << 30, tmp
assert os.stat("/tmp").st_dev != os.stat("/").st_dev
print("root: 1 GiB tmpfs-backed overlay; /tmp: separate 1 GiB tmpfs")
