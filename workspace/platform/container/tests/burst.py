#!/usr/bin/env python3
"""Measure node-local cached starts with scheduled arrivals and overlapping VMs."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import statistics
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--daemon", default="http://127.0.0.1:8000")
parser.add_argument(
    "--image",
    default="localhost/workspace-storage:2g",
    help="May contain {i} for distinct images",
)
parser.add_argument("--count", type=int, default=100)
parser.add_argument("--arrival-seconds", type=float, default=10)
parser.add_argument("--hold-seconds", type=float, default=5)
parser.add_argument(
    "--init-read-mib",
    type=int,
    default=0,
    help="Read and hash fixture data during initialization",
)
parser.add_argument("--min-available-gib", type=float, default=16)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.count < 1 or args.arrival_seconds < 0 or args.hold_seconds < 0:
    parser.error("count must be positive and durations nonnegative")


def request(path, body=None):
    try:
        with urlopen(
            Request(
                args.daemon + path,
                data=json.dumps(body or {}).encode(),
                headers={"content-type": "application/json"},
            ),
            timeout=180,
        ) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"HTTP {error.code}: {error.read().decode()}") from error


def available_memory():
    return (
        int(
            next(
                line.split()[1]
                for line in Path("/proc/meminfo").read_text().splitlines()
                if line.startswith("MemAvailable:")
            )
        )
        * 1024
    )


observations = []
monitor_done = threading.Event()


def monitor():
    while not monitor_done.is_set():
        observations.append(
            {
                "seconds": time.monotonic() - epoch,
                "available_bytes": available_memory(),
                "cpu_ticks": list(
                    map(
                        int, Path("/proc/stat").read_text().splitlines()[0].split()[1:9]
                    )
                ),
            }
        )
        monitor_done.wait(0.25)


identities = [str(uuid.uuid4()) for _ in range(args.count)]
epoch = time.monotonic()
watcher = threading.Thread(target=monitor)
watcher.start()


def sample(i):
    scheduled = i * args.arrival_seconds / args.count
    time.sleep(max(0, epoch + scheduled - time.monotonic()))
    row = {
        "workspace_uuid": identities[i],
        "image": args.image.format(i=i),
        "scheduled_seconds": scheduled,
    }
    if available_memory() < args.min_available_gib * (1 << 30):
        return row | {"error": "host memory headroom reached; start skipped"}
    start = time.monotonic()
    row["submitted_seconds"] = start - epoch
    try:
        config = {"container_image_ref": row["image"]}
        if args.init_read_mib:
            config["entrypoint"] = [
                "python3",
                "-c",
                """
import hashlib, pathlib, sys
remaining = int(sys.argv[1]) << 20
digest = hashlib.sha256()
for path in sorted(pathlib.Path("/benchmark").glob("layer*")):
    with path.open("rb") as source:
        while remaining and (data := source.read(min(1 << 20, remaining))):
            digest.update(data)
            remaining -= len(data)
    if not remaining:
        break
assert remaining == 0
""",
                str(args.init_read_mib),
            ]
        request(
            f"/api/workspaces/{identities[i]}/start",
            {
                "runtime_config": config,
                "volume": {
                    "volume_uuid": identities[i],
                    "dst_path": "/home/hacker",
                    "max_size_bytes": 1 << 30,
                },
            },
        )
        row["start_seconds"] = time.monotonic() - start
        row["ready_seconds"] = time.monotonic() - epoch
        executed = request(
            f"/w/{identities[i]}/exec/", {"argv": ["/bin/sh", "-c", "printf ready"]}
        )
        assert executed == {"exit_code": 0, "stdout": "ready", "stderr": ""}, executed
        row["usable_seconds"] = time.monotonic() - start
    except Exception as error:
        row["error"] = str(error)
    print(json.dumps(row), flush=True)
    return row


rows = []
cleanup_errors = []


def cleanup(identity):
    try:
        request(f"/api/workspaces/{identity}/stop")
        request(f"/api/volumes/{identity}/delete")
    except Exception as error:
        return {"workspace_uuid": identity, "error": str(error)}


try:
    with ThreadPoolExecutor(max_workers=args.count) as pool:
        rows = list(pool.map(sample, range(args.count)))
    time.sleep(args.hold_seconds)
finally:
    monitor_done.set()
    watcher.join()
    with ThreadPoolExecutor(max_workers=8) as pool:
        cleanup_errors = [error for error in pool.map(cleanup, identities) if error]
    successful = [row for row in rows if "error" not in row]
    timings = sorted(row["start_seconds"] for row in successful)
    summary = {
        "successes": len(successful),
        "failures": len(rows) - len(successful),
        "minimum_available_gib": min(row["available_bytes"] for row in observations)
        / (1 << 30),
    }
    if timings:
        summary.update(
            median_seconds=statistics.median(timings),
            p95_seconds=timings[math.ceil(len(timings) * 0.95) - 1],
            maximum_seconds=timings[-1],
            last_ready_seconds=max(row["ready_seconds"] for row in successful),
            p95_usable_seconds=sorted(row["usable_seconds"] for row in successful)[
                math.ceil(len(timings) * 0.95) - 1
            ],
        )
    result = {
        "image": args.image,
        "count": args.count,
        "arrival_seconds": args.arrival_seconds,
        "init_read_mib": args.init_read_mib,
        "summary": summary,
        "starts": rows,
        "host": observations,
        "cleanup_errors": cleanup_errors,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
if summary["failures"] or cleanup_errors:
    raise SystemExit(1)
