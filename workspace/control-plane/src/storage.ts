import { Context, Effect, Layer } from "effect";
import { Environment } from "./common.ts";
import { fromPromise, workspaceError } from "./workspaces/errors.ts";
import { transferUrl, verifyTransferURL } from "./volumes/transfers.ts";

const SNAPSHOT_PART_SIZE = 5 * 1024 * 1024;

// Btrfs send streams have no Content-Length. R2 requires each uploaded part to
// have a known length, so buffer one part at a time instead of the whole home.
async function storeSnapshotStream(bucket: R2Bucket, key: string, body: ReadableStream<Uint8Array>) {
  const reader = body.getReader();
  const buffer = new Uint8Array(SNAPSHOT_PART_SIZE);
  let used = 0;
  let upload: R2MultipartUpload | undefined;
  const parts: R2UploadedPart[] = [];
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      let offset = 0;
      while (offset < value.length) {
        const length = Math.min(buffer.length - used, value.length - offset);
        buffer.set(value.subarray(offset, offset + length), used);
        used += length;
        offset += length;
        if (used === buffer.length) {
          upload ??= await bucket.createMultipartUpload(key);
          parts.push(await upload.uploadPart(parts.length + 1, buffer));
          used = 0;
        }
      }
    }
    if (!upload) {
      await bucket.put(key, buffer.subarray(0, used));
    } else {
      if (used > 0) parts.push(await upload.uploadPart(parts.length + 1, buffer.subarray(0, used)));
      await upload.complete(parts);
    }
  } catch (error) {
    await upload?.abort().catch(() => undefined);
    throw error;
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

function committedSnapshotKey(volumeUUID: string, snapshotUUID: string) {
  return `snapshots/${volumeUUID}/${snapshotUUID}`;
}

function stagingSnapshotKey(volumeUUID: string, snapshotUUID: string, uploadUUID: string) {
  return `staging/${volumeUUID}/${snapshotUUID}/${uploadUUID}`;
}

async function commitStagedSnapshot(
  bucket: R2Bucket,
  volumeUUID: string,
  snapshotUUID: string,
  uploadUUID: string,
) {
  const stagingKey = stagingSnapshotKey(volumeUUID, snapshotUUID, uploadUUID);
  const committedKey = committedSnapshotKey(volumeUUID, snapshotUUID);
  const stagingObject = await bucket.get(stagingKey);
  if (!stagingObject) return false;

  await bucket.put(committedKey, stagingObject.body);
  const committed = await bucket.head(committedKey);
  if (!committed) return false;

  await bucket.delete(stagingKey).catch(() => undefined);
  return true;
}

export class SnapshotStore extends Context.Service<SnapshotStore>()("control-plane/SnapshotStore", {
  make: Effect.gen(function*() {
    const env = yield* Environment;
    const bucket = env.VOLUMES;
    return {
      read: (volumeUUID: string, snapshotUUID: string) =>
        fromPromise(() => bucket.get(committedSnapshotKey(volumeUUID, snapshotUUID))).pipe(
          Effect.flatMap((object) => object
            ? Effect.succeed(object.body)
            : Effect.fail(workspaceError("snapshot_not_found", "Snapshot not found", 404))),
        ),
      upload: (volumeUUID: string, snapshotUUID: string, uploadUUID: string, body: ReadableStream<Uint8Array>) => {
        const key = stagingSnapshotKey(volumeUUID, snapshotUUID, uploadUUID);
        return fromPromise(() => storeSnapshotStream(bucket, key, body)).pipe(Effect.as(key));
      },
      commit: (volumeUUID: string, snapshotUUID: string, uploadUUID: string) =>
        fromPromise(() => commitStagedSnapshot(bucket, volumeUUID, snapshotUUID, uploadUUID)).pipe(
          Effect.flatMap((committed) => committed ? Effect.void : Effect.fail(workspaceError("volume_reclaim_failed"))),
        ),
      transferUrl: (method: "GET" | "PUT", volumeUUID: string, snapshotUUID: string, uploadUUID?: string) =>
        fromPromise(() => transferUrl(env, method, volumeUUID, snapshotUUID, uploadUUID)),
      verifyTransfer: (requestURL: string, method: "GET" | "PUT") =>
        fromPromise(() => verifyTransferURL(env, requestURL, method)).pipe(
          Effect.flatMap((valid) => valid
            ? Effect.void
            : Effect.fail(workspaceError("invalid_signature", "Invalid transfer signature", 401))),
        ),
    };
  }),
}) {
  static readonly layer = Layer.effect(SnapshotStore, SnapshotStore.make);
}
