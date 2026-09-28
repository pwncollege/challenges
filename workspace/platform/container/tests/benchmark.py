#!/usr/bin/env python3
"""Measure cached workspace starts and verify layer sharing through the node API."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import statistics
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--daemon", default="http://127.0.0.1:8000")
parser.add_argument("--image", default="localhost/workspace-storage:2g")
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--runs", type=int, default=5)
parser.add_argument("--concurrency", type=int, default=4)
args = parser.parse_args()


def request(path, body=None):
    data = json.dumps(body or {}).encode()
    try:
        with urlopen(
            Request(
                args.daemon + path,
                data=data,
                headers={"content-type": "application/json"},
            ),
            timeout=180,
        ) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"{path}: HTTP {error.code}: {error.read().decode()}"
        ) from error


def execute(identity, script):
    result = request(f"/w/{identity}/exec/", {"argv": ["python3", "-c", script]})
    assert result["exit_code"] == 0, result
    return result["stdout"]


def sample(_):
    identity = str(uuid.uuid4())
    start = time.monotonic()
    try:
        request(
            f"/api/workspaces/{identity}/start",
            {"runtime_config": {"container_image_ref": args.image}},
        )
        ready = time.monotonic() - start
        result = json.loads(
            execute(
                identity,
                """
import hashlib, json, os, time
from pathlib import Path
root = Path("/benchmark")
assert (root / "version.txt").read_text() == "3"
assert not (root / "removed.txt").exists()
assert not (root / "isolation.txt").exists()
(root / "isolation.txt").write_text("private")
target = root / "layer0-0000"
assert target.read_bytes() == bytes(4 << 20)
start = time.monotonic()
with target.open("r+b") as output:
    output.write(b"X")
    output.flush()
    os.fsync(output.fileno())
copyup = time.monotonic() - start
start = time.monotonic()
digest = hashlib.sha256()
size = 0
for path in sorted(root.glob("layer*")):
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
            size += len(chunk)
elapsed = time.monotonic() - start
mounts = Path("/proc/mounts").read_text().splitlines()
print(json.dumps({"read_seconds": elapsed, "read_bytes": size, "sha256": digest.hexdigest(), "copyup_fsync_seconds": copyup, "root_mount": next(line for line in mounts if line.split()[1] == "/"), "root_capacity": os.statvfs("/").f_blocks * os.statvfs("/").f_frsize}))
""",
            )
        )
        result["start_seconds"] = ready
        return result
    finally:
        request(f"/api/workspaces/{identity}/stop")


sequential = [sample(i) for i in range(args.runs)]
start = time.monotonic()
with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
    concurrent = list(pool.map(sample, range(args.concurrency)))
assert len({row["sha256"] for row in sequential + concurrent}) == 1
result = {
    "backend": "erofs",
    "image": args.image,
    "sequential": sequential,
    "concurrent": concurrent,
    "concurrent_wall_seconds": time.monotonic() - start,
}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(
    json.dumps(
        {
            "backend": "erofs",
            "median_start_seconds": statistics.median(
                row["start_seconds"] for row in sequential
            ),
            "concurrent_start_seconds": [row["start_seconds"] for row in concurrent],
        },
        indent=2,
    )
)
