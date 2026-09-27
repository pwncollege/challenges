import assert from "node:assert/strict";
import test from "node:test";
import { Effect } from "effect";
import { AwsClient } from "aws4fetch";
import { createBindings, loadModule, runEffect, snapshotBindings } from "./helpers.mjs";

const { snapshotUrl, Environment } = await loadModule("tests/fixtures/services.ts");
async function setup(t) {
  const result = await createBindings(t);
  return { ...result, transferUrl: (method, volume, snapshot) =>
    runEffect(snapshotUrl(method, volume, snapshot).pipe(Effect.provideService(Environment, result.bindings))) };
}

for (const size of [13, 5 * 1024 * 1024, 10 * 1024 * 1024 + 13]) {
  test(`presigned S3 PUT and GET preserve ${size} snapshot bytes`, async (t) => {
    const { VOLUMES, transferUrl } = await setup(t);
    const volume = crypto.randomUUID(), snapshot = crypto.randomUUID();
    const contents = Uint8Array.from({ length: size }, (_, index) => index % 251);
    const put = await transferUrl("PUT", volume, snapshot);
    const url = new URL(put);
    assert.equal(url.pathname, `/cdn-cgi/local/r2/s3/volumes/snapshots/${volume}/${snapshot}`);
    assert.equal(url.searchParams.get("X-Amz-Expires"), "900");
    assert.equal(url.searchParams.get("X-Amz-SignedHeaders"), "host");
    const response = await fetch(put, { method: "PUT", body: contents });
    assert.equal(response.status, 200, await response.text());
    assert.equal((await VOLUMES.head(`snapshots/${volume}/${snapshot}`)).size, size);
    const downloaded = await fetch(await transferUrl("GET", volume, snapshot));
    assert.equal(downloaded.status, 200);
    assert.deepEqual(new Uint8Array(await downloaded.arrayBuffer()), contents);
  });
}

test("presigned transfers are bound to the method, object, credentials, and expiry", async (t) => {
  const { VOLUMES, transferUrl } = await setup(t);
  const volume = crypto.randomUUID(), snapshot = crypto.randomUUID();
  const put = await transferUrl("PUT", volume, snapshot);
  const changed = new URL(put);
  changed.pathname += "-different";
  const expired = new URL(put);
  expired.search = "?X-Amz-Expires=1";
  const client = new AwsClient({
    service: "s3", region: "auto",
    accessKeyId: snapshotBindings.PWN_WORKSPACE_R2_ACCESS_KEY_ID,
    secretAccessKey: snapshotBindings.PWN_WORKSPACE_R2_SECRET_ACCESS_KEY,
  });
  const old = await client.sign(expired.toString(), {
    method: "PUT", aws: { signQuery: true, datetime: "20200101T000000Z" },
  });
  const invalid = new URL(put);
  invalid.searchParams.set("X-Amz-Signature", "0".repeat(64));
  for (const [url, method] of [[put, "GET"], [changed, "PUT"], [old.url, "PUT"], [invalid, "PUT"]]) {
    const response = await fetch(url.toString(), { method, ...(method === "PUT" ? { body: "no" } : {}) });
    assert.equal(response.status, 403, await response.text());
  }
  assert.equal((await VOLUMES.list()).objects.length, 0);
});

test("production transfer URLs address the R2 S3 endpoint", async () => {
  const url = new URL(await runEffect(snapshotUrl("PUT", "volume", "snapshot").pipe(Effect.provideService(Environment, {
    ...snapshotBindings, PWN_WORKSPACE_R2_BUCKET_URL: "https://account.r2.cloudflarestorage.com/volumes",
  }))));
  assert.equal(url.host, "account.r2.cloudflarestorage.com");
  assert.equal(url.pathname, "/volumes/snapshots/volume/snapshot");
});
