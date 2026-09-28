#!/usr/bin/env python3
"""Extend a ctr-exported Alpine OCI archive with a reproducible storage workload."""

import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import random
import tarfile
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("base", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--gib", type=int, default=2)
args = parser.parse_args()
reference = f"localhost/workspace-storage:{args.gib}g"

with tempfile.TemporaryDirectory(dir=args.output.parent) as temporary:
    root = Path(temporary)
    with tarfile.open(args.base) as archive:
        archive.extractall(root, filter="data")

    def read_blob(descriptor):
        return json.loads(
            (root / "blobs/sha256" / descriptor["digest"].split(":")[1]).read_bytes()
        )

    descriptor = json.loads((root / "index.json").read_text())["manifests"][0]
    manifest = read_blob(descriptor)
    while "manifests" in manifest:
        descriptor = next(
            d
            for d in manifest["manifests"]
            if d.get("platform", {}).get("architecture") == "amd64"
        )
        manifest = read_blob(descriptor)
    manifest = copy.deepcopy(manifest)
    config = read_blob(manifest["config"])

    def blob(data, media):
        digest = hashlib.sha256(data).hexdigest()
        (root / "blobs/sha256" / digest).write_bytes(data)
        return {"mediaType": media, "digest": "sha256:" + digest, "size": len(data)}

    class HashWriter:
        def __init__(self, destination):
            self.destination = destination
            self.digest = hashlib.sha256()

        def write(self, data):
            self.digest.update(data)
            return self.destination.write(data)

    for layer in range(4):
        path = root / "layer.gz"
        with (
            path.open("wb") as raw,
            gzip.GzipFile(
                fileobj=raw, mode="wb", compresslevel=1, mtime=0
            ) as compressed,
        ):
            writer = HashWriter(compressed)
            with tarfile.open(fileobj=writer, mode="w|") as archive:

                def add(name, data=b"", directory=False):
                    entry = tarfile.TarInfo(name)
                    entry.uid = entry.gid = 1000
                    entry.mode = 0o755 if directory else 0o644
                    entry.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
                    entry.size = len(data)
                    archive.addfile(entry, io.BytesIO(data))

                if layer == 0:
                    add("benchmark", directory=True)
                    add("benchmark/removed.txt", b"must be hidden by a whiteout")
                add("benchmark/version.txt", str(layer).encode())
                if layer == 1:
                    add("benchmark/.wh.removed.txt")
                rng = random.Random(layer)
                # The 2 GiB workload is half incompressible, half zero-filled.
                # Larger fixtures use zeros to test capacity without huge archives;
                # their compression ratio is not a representative benchmark.
                for number in range(args.gib * 64):
                    data = (
                        rng.randbytes(4 << 20)
                        if args.gib == 2 and number % 2
                        else bytes(4 << 20)
                    )
                    add(f"benchmark/layer{layer}-{number:04d}", data)
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        size = path.stat().st_size
        path.rename(root / "blobs/sha256" / digest)
        manifest["layers"].append(
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": "sha256:" + digest,
                "size": size,
            }
        )
        config["rootfs"]["diff_ids"].append("sha256:" + writer.digest.hexdigest())
        config.setdefault("history", []).append(
            {"created_by": "workspace storage comparison"}
        )
        print(f"prepared layer {layer + 1}/4", flush=True)

    manifest["config"] = blob(
        json.dumps(config).encode(), "application/vnd.oci.image.config.v1+json"
    )
    descriptor = blob(
        json.dumps(manifest).encode(), "application/vnd.oci.image.manifest.v1+json"
    )
    descriptor["annotations"] = {
        "io.containerd.image.name": reference,
        "org.opencontainers.image.ref.name": reference,
    }
    (root / "index.json").write_text(
        json.dumps({"schemaVersion": 2, "manifests": [descriptor]})
    )
    (root / "oci-layout").write_text('{"imageLayoutVersion":"1.0.0"}')
    with tarfile.open(args.output, "w") as archive:
        for path in [root / "index.json", root / "oci-layout", root / "blobs"]:
            archive.add(path, arcname=path.name)
print(reference)
