import assert from "node:assert/strict";
import test from "node:test";
import { Context, Effect, Layer } from "effect";
import { createBindings, loadModule } from "./helpers.mjs";

const { handler, Environment, WorkerContext, NodeClient, SnapshotStore, WorkspaceStore } =
  await loadModule("tests/fixtures/services.ts");
const userUUID = "11111111-1111-4111-8111-111111111111";
const nodeUUID = "33333333-3333-4333-8333-333333333333";
const key = await crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"]);
const keys = {
  PWN_WORKSPACE_PRIVATE_KEY_B64: Buffer.from(await crypto.subtle.exportKey("pkcs8", key.privateKey)).toString("base64"),
  PWN_WORKSPACE_PUBLIC_KEY_B64: Buffer.from(await crypto.subtle.exportKey("spki", key.publicKey)).toString("base64"),
};
const payload = { node_uuid: nodeUUID, runtime_config: { container_image_ref: "test" } };

async function setup(t, nodes, { failCommit = false } = {}) {
  const { DB, VOLUMES } = await createBindings(t);
  const background = [];
  let batches = 0;
  const database = {
    prepare: (...args) => DB.prepare(...args),
    batch: (...args) => {
      batches++;
      if (failCommit && batches === 2) return Promise.reject(new Error("D1 unavailable"));
      return DB.batch(...args);
    },
  };
  const env = { DB: database, VOLUMES, ...keys, PWN_WORKSPACE_ENVIRONMENT: "development", PWN_WORKSPACE_ORIGIN: "https://control.test" };
  const services = await Effect.runPromise(Effect.scoped(Layer.build(Layer.mergeAll(
    WorkspaceStore.layer, SnapshotStore.layer, nodes ? Layer.succeed(NodeClient, nodes) : NodeClient.layer,
  ).pipe(Layer.provideMerge(Layer.succeed(Environment, env))))));
  const context = Context.add(services, WorkerContext, { waitUntil(promise) { background.push(promise); } });
  const fetch = (path, options) => handler(new Request(`https://control.test${path}`, options), context);
  const login = await fetch("/api/login", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ user_uuid: userUUID }),
  });
  assert.equal(login.status, 200);
  const cookie = login.headers.get("set-cookie").split(";")[0];
  const post = (path, body, options = {}) => fetch(path, {
    method: "POST", headers: { "content-type": "application/json", cookie }, body: JSON.stringify(body), ...options,
  });
  return { DB, fetch, post, background, batches: () => batches };
}

test("Effect HTTP boundary rejects malformed payloads and invalid transfer signatures", async (t) => {
  const { DB, fetch, post } = await setup(t);
  for (const body of ["{", "null", "{}", JSON.stringify({ user_uuid: "invalid" })]) {
    const response = await post("/api/login", undefined, { body });
    assert.equal(response.status, 400);
    assert.equal((await response.json()).error.code, "invalid_request");
  }
  for (const body of [
    {}, { ...payload, node_uuid: "invalid" },
    { ...payload, runtime_config: { container_image_ref: "" } },
    { ...payload, runtime_config: { container_image_ref: "test", entrypoint: [1] } },
    { ...payload, runtime_config: { container_image_ref: "test", env: { X: 1 } } },
    ...["/", "/etc", "relative", "/home/../etc"].map((volume_dst_path) => ({ ...payload, volume_dst_path })),
  ]) {
    const response = await post("/api/workspaces/start", body);
    assert.equal(response.status, 400, JSON.stringify(body));
    assert.equal((await response.json()).error.code, "invalid_request");
  }
  for (const path of ["/api/workspaces/start", "/api/workspaces/stop"]) {
    const response = await fetch(path, { method: "POST" });
    assert.equal(response.status, 401);
    assert.equal((await response.json()).error.code, "unauthorized");
  }
  for (const method of ["GET", "PUT"]) {
    const response = await fetch(`/api/volumes/${crypto.randomUUID()}/snapshots/${crypto.randomUUID()}?expires=9999999999&signature=invalid`, { method });
    assert.equal(response.status, 401);
    assert.equal((await response.json()).error.code, "invalid_signature");
  }
  assert.equal(await DB.prepare("SELECT COUNT(*) FROM workspaces").first("COUNT(*)"), 0);
  assert.equal(await DB.prepare("SELECT COUNT(*) FROM workspace_operations").first("COUNT(*)"), 0);
});

test("disconnecting the NDJSON reader does not cancel or roll back a start", async (t) => {
  const starting = Promise.withResolvers();
  const started = Promise.withResolvers();
  t.after(() => started.resolve());
  const calls = [];
  const { DB, post, background } = await setup(t, {
    stopWorkspace: () => Effect.sync(() => { calls.push("stop"); }),
    startWorkspace: () => Effect.promise(async () => {
      calls.push("start");
      starting.resolve();
      await started.promise;
    }),
  });
  const response = await post("/api/workspaces/start", payload);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "application/x-ndjson");
  await starting.promise;
  await response.body.cancel();
  started.resolve();
  await Promise.all(background);
  assert.deepEqual(calls, ["start"]);
  assert.equal(await DB.prepare("SELECT status FROM workspaces").first("status"), "running");
  assert.equal(await DB.prepare("SELECT COUNT(*) FROM workspace_operations").first("COUNT(*)"), 0);
});

test("disconnecting during a node stop still records the stop and releases its claim", async (t) => {
  const stopping = Promise.withResolvers();
  const stopped = Promise.withResolvers();
  t.after(() => stopped.resolve());
  const { DB, post } = await setup(t, {
    stopWorkspace: () => Effect.promise(async (signal) => {
      stopping.resolve();
      await stopped.promise;
      assert.equal(signal.aborted, false);
    }),
  });
  await DB.batch([
    DB.prepare("INSERT INTO workspaces VALUES (1, ?, 1, 'test', '{}', 'running', 0, 0)").bind(crypto.randomUUID()),
    DB.prepare("INSERT INTO user_workspaces VALUES (1, 1)"),
  ]);
  const controller = new AbortController();
  const response = post("/api/workspaces/stop", undefined, { signal: controller.signal });
  await stopping.promise;
  controller.abort();
  stopped.resolve();
  await response;
  assert.equal(await DB.prepare("SELECT COUNT(*) FROM workspaces").first("COUNT(*)"), 0);
  assert.equal(await DB.prepare("SELECT COUNT(*) FROM workspace_operations").first("COUNT(*)"), 0);
});

for (const outcome of ["success", "node-timeout", "commit-failure"]) {
  test(`start request count and claim retention: ${outcome}`, async (t) => {
    let commands = 0;
    const { DB, post, batches } = await setup(t, {
      startWorkspace: () => Effect.suspend(() => {
        commands++;
        return outcome === "node-timeout" ? Effect.fail(new Error("response lost")) : Effect.void;
      }),
    }, { failCommit: outcome === "commit-failure" });
    const response = await post("/api/workspaces/start", payload);
    const events = await response.text();
    assert.equal(commands, 1);
    assert.equal(batches(), outcome === "node-timeout" ? 1 : 2);
    if (outcome === "success") {
      assert.match(events, /"event":"complete"/);
      assert.equal(await DB.prepare("SELECT COUNT(*) FROM workspace_operations").first("COUNT(*)"), 0);
    } else {
      assert.match(events, /"event":"error"/);
      const pending = await DB.prepare("SELECT operation_uuid, plan_json FROM workspace_operations").first();
      assert.ok(pending.operation_uuid);
      assert.ok(JSON.parse(pending.plan_json).snapshot_uuid);
      const retry = await post("/api/workspaces/start", payload);
      assert.match(await retry.text(), /workspace_operation_in_progress/);
      assert.equal(commands, 1);
    }
  });
}
