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
