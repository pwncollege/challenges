import assert from "node:assert/strict";
import test from "node:test";
import { build } from "esbuild";
import { createBindings, loadModule } from "./helpers.mjs";

const { transferUrl } = await loadModule("src/volumes/transfers.ts");
const bundle = await build({ entryPoints: ["src/index.ts"], bundle: true, format: "esm", write: false });
const key = await crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"]);
const bindings = {
  PWN_WORKSPACE_PRIVATE_KEY_B64: Buffer.from(await crypto.subtle.exportKey("pkcs8", key.privateKey)).toString("base64"),
  PWN_WORKSPACE_PUBLIC_KEY_B64: Buffer.from(await crypto.subtle.exportKey("spki", key.publicKey)).toString("base64"),
  PWN_WORKSPACE_ORIGIN: "https://control.test",
};

for (const size of [13, 5 * 1024 * 1024, 10 * 1024 * 1024 + 13]) {
  test(`streaming ${size} snapshot bytes directly to R2 preserves contents`, async (t) => {
    const { mf, VOLUMES } = await createBindings(t, { script: bundle.outputFiles[0].text, bindings });
    const volume = crypto.randomUUID(), snapshot = crypto.randomUUID();
    const contents = Uint8Array.from({ length: size }, (_, index) => index % 251);
    const url = await transferUrl(bindings, "PUT", volume, snapshot);
    const response = await mf.dispatchFetch(url, { method: "PUT", body: contents, headers: { "content-length": String(size) } });
    assert.equal(response.status, 200, await response.text());
    const object = await VOLUMES.get(`snapshots/${volume}/${snapshot}`);
    assert.equal(object.size, size);
    assert.deepEqual(new Uint8Array(await object.arrayBuffer()), contents);
  });
}

test("uploads require a known length before writing to R2", async (t) => {
  const { mf, VOLUMES } = await createBindings(t, { script: bundle.outputFiles[0].text, bindings });
  const volume = crypto.randomUUID(), snapshot = crypto.randomUUID();
  const url = await transferUrl(bindings, "PUT", volume, snapshot);
  const body = new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(13)); controller.close(); } });
  const response = await mf.dispatchFetch(url, { method: "PUT", body, duplex: "half" });
  assert.equal(response.status, 411, await response.text());
  assert.equal(await VOLUMES.head(`snapshots/${volume}/${snapshot}`), null);
});
