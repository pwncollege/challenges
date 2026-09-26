import type { Bindings } from "./common.ts";

const SNAPSHOT_PART_SIZE = 5 * 1024 * 1024;

// Btrfs send streams have no Content-Length. R2 requires each uploaded part to
// have a known length, so buffer one part at a time instead of the whole home.
export async function storeSnapshotStream(bucket: R2Bucket, key: string, body: ReadableStream<Uint8Array>) {
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

export function committedSnapshotKey(volumeUUID: string, snapshotUUID: string) {
  return `snapshots/${volumeUUID}/${snapshotUUID}`;
}

export function stagingSnapshotKey(volumeUUID: string, snapshotUUID: string, uploadUUID: string) {
  return `staging/${volumeUUID}/${snapshotUUID}/${uploadUUID}`;
}

export async function commitStagedSnapshot(
  env: Bindings,
  volumeUUID: string,
  snapshotUUID: string,
  uploadUUID: string,
) {
  const stagingKey = stagingSnapshotKey(volumeUUID, snapshotUUID, uploadUUID);
  const committedKey = committedSnapshotKey(volumeUUID, snapshotUUID);
  const stagingObject = await env.VOLUMES.get(stagingKey);
  if (!stagingObject) return false;

  await env.VOLUMES.put(committedKey, stagingObject.body);
  const committed = await env.VOLUMES.head(committedKey);
  if (!committed) return false;

  await env.VOLUMES.delete(stagingKey).catch(() => undefined);
  return true;
}
