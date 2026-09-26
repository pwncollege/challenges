import assert from "node:assert/strict";
import test from "node:test";
import { Effect, Fiber, Layer } from "effect";
import { loadModule, runEffect } from "./helpers.mjs";

const { NodeClient, Environment, FetchHttpClient } = await loadModule("tests/fixtures/services.ts");
const key = await crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"]);
const privateKey = Buffer.from(await crypto.subtle.exportKey("pkcs8", key.privateKey)).toString("base64");
const node = { nodeId: 1, nodeUUID: crypto.randomUUID(), baseUrl: "https://node.test" };
const workspaceUUID = crypto.randomUUID();
const volumeUUID = crypto.randomUUID();
const startBody = {
  runtime_config: { container_image_ref: "test", entrypoint: ["/bin/sh"], env: { VALUE: "a\\nb" } },
  volume: { volume_uuid: volumeUUID, dst_path: "/home/hacker", max_size_bytes: 1073741824, snapshot: null },
};

function clientLayer(fetch) {
  return NodeClient.layer.pipe(Layer.provide(Layer.mergeAll(
    Layer.succeed(Environment, { PWN_WORKSPACE_PRIVATE_KEY_B64: privateKey }),
    Layer.succeed(FetchHttpClient.Fetch, fetch),
  )));
}

function execute(fetch, operation) {
  return runEffect(Effect.flatMap(NodeClient, operation).pipe(Effect.provide(clientLayer(fetch))));
}

test("node commands sign exactly the method, URL, and body sent to the daemon", async () => {
  let calls = 0;
  await execute(async (url, options) => {
    calls++;
    assert.equal(options.method, "POST");
    assert.equal(url.toString(), `https://node.test/api/workspaces/${workspaceUUID}/start`);
    assert.deepEqual(JSON.parse(options.body), startBody);
    const hash = Buffer.from(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(options.body))).toString("hex");
    const canonical = `POST\n${url.pathname}${url.search}\n${options.headers["x-pwn-workspace-timestamp"]}\n${hash}`;
    assert.ok(await crypto.subtle.verify(
      "Ed25519", key.publicKey,
      Buffer.from(options.headers["x-pwn-workspace-signature"], "base64"),
      new TextEncoder().encode(canonical),
    ));
    return new Response(null, { status: 200 });
  }, (nodes) => nodes.startWorkspace(node, workspaceUUID, startBody));
  assert.equal(calls, 1);
});

for (const [name, body, code, message] of [
  ["valid error", { error: { code: "image_not_available", message: "Pull the image first" } }, "image_not_available", "Pull the image first"],
  ["invalid fields", { error: { code: 123, message: [] } }, "workspace_start_failed", "workspace_start_failed"],
  ["missing error", {}, "workspace_start_failed", "workspace_start_failed"],
  ["invalid JSON", "not json", "workspace_start_failed", "workspace_start_failed"],
]) {
  test(`node start returns a typed error for ${name}`, async () => {
    let calls = 0;
    await assert.rejects(() => execute(async () => {
      calls++;
      return new Response(typeof body === "string" ? body : JSON.stringify(body), { status: 409 });
    }, (nodes) => nodes.startWorkspace(node, workspaceUUID, startBody)), { _tag: "WorkspaceError", code, message, status: 409 });
    assert.equal(calls, 1, "mutating commands must not be retried automatically");
  });
}

test("missing routes fail; the daemon acknowledges an absent workspace with 200", async () => {
  const missing = async () => new Response(null, { status: 404 });
  await assert.rejects(() => execute(missing, (nodes) => nodes.stopWorkspace(node, workspaceUUID)),
    { code: "workspace_stop_failed" });
  await assert.rejects(() => execute(missing, (nodes) => nodes.startWorkspace(node, workspaceUUID, startBody)),
    { code: "workspace_start_failed", status: 404 });
  await assert.rejects(() => execute(missing, (nodes) => nodes.exportVolume(node, volumeUUID, workspaceUUID, "https://control.test/upload")),
    { code: "volume_export_failed", status: 500 });
  await assert.rejects(() => execute(async () => new Response(null, { status: 503 }),
    (nodes) => nodes.stopWorkspace(node, workspaceUUID)), { code: "workspace_stop_failed", status: 500 });
});

test("a transport failure is typed and is not retried", async () => {
  let calls = 0;
  await assert.rejects(() => execute(async () => {
    calls++;
    throw new Error("connection lost");
  }, (nodes) => nodes.stopWorkspace(node, workspaceUUID)), { code: "node_unavailable", status: 502 });
  assert.equal(calls, 1);
});

test("interrupting a node request aborts its transport", async () => {
  const requesting = Promise.withResolvers();
  let aborted = false;
  const fiber = Effect.runFork(Effect.flatMap(NodeClient, (nodes) => nodes.stopWorkspace(node, workspaceUUID)).pipe(
    Effect.provide(clientLayer((_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => {
        aborted = true;
        reject(new Error("aborted"));
      }, { once: true });
      requesting.resolve();
    }))),
  ));
  await requesting.promise;
  await Effect.runPromise(Fiber.interrupt(fiber));
  assert.equal(aborted, true);
});
