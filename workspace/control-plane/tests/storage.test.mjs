import assert from "node:assert/strict";
import test from "node:test";
import { createBindings, loadModule } from "./helpers.mjs";

const { storeSnapshotStream } = await loadModule("src/storage.ts");
const PART_SIZE = 5 * 1024 * 1024;

for (const size of [0, 13, PART_SIZE, 2 * PART_SIZE + 13]) {
  test(`streaming ${size} snapshot bytes preserves contents in R2`, async (t) => {
    const { VOLUMES } = await createBindings(t);
    const contents = Uint8Array.from({ length: size }, (_, index) => index % 251);
    const body = new ReadableStream({
      start(controller) {
        // Deliberately split across part boundaries and send a chunk larger than a part.
        controller.enqueue(contents.subarray(0, 3));
        controller.enqueue(contents.subarray(3, size - 1));
        controller.enqueue(contents.subarray(Math.max(3, size - 1)));
        controller.close();
      },
    });
    await storeSnapshotStream(VOLUMES, "snapshot", body);
    const object = await VOLUMES.get("snapshot");
    assert.equal(object.size, size);
    assert.deepEqual(new Uint8Array(await object.arrayBuffer()), contents);
  });
}

test("failed multipart uploads abort and cancel the source stream", async () => {
  let aborted = false;
  let cancelled = false;
  const failure = new Error("storage unavailable");
  const upload = {
    uploadPart: async () => { throw failure; },
    abort: async () => { aborted = true; },
    complete: async () => assert.fail("failed upload must not complete"),
  };
  const bucket = { createMultipartUpload: async () => upload };
  const body = new ReadableStream({
    pull(controller) { controller.enqueue(new Uint8Array(PART_SIZE)); },
    cancel() { cancelled = true; },
  });
  await assert.rejects(() => storeSnapshotStream(bucket, "snapshot", body), failure);
  assert.equal(aborted, true);
  assert.equal(cancelled, true);
});
