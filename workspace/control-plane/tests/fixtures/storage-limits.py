"""Both writable filesystems reject allocation beyond their independent limits."""

import errno
import os
from pathlib import Path

for directory in ["/run/workspace/user", "/tmp"]:
    path = Path(directory) / "storage-limit-test"
    try:
        with path.open("wb") as output:
            try:
                os.posix_fallocate(output.fileno(), 0, (1 << 30) + 4096)
            except OSError as error:
                assert error.errno == errno.ENOSPC, error
            else:
                raise AssertionError(f"{directory} accepted more than 1 GiB")
    finally:
        path.unlink(missing_ok=True)
    path.write_text("writes recover after releasing the allocation")
    path.unlink()
    print(f"{directory}: allocation limit enforced, writes recover")
