import assert from "node:assert/strict";
import test from "node:test";
import { build } from "esbuild";
import { createBindings, loadModule } from "./helpers.mjs";

import { Schema } from "effect";
const { WorkspaceEvent } = await loadModule("tests/fixtures/services.ts");
const decodeEvent = Schema.decodeUnknownSync(WorkspaceEvent);

const bundle = await build({ entryPoints: ["src/index.ts"], bundle: true, format: "esm", write: false });
const userUUID = "11111111-1111-4111-8111-111111111111";
const targetNodeUUID = "44444444-4444-4444-8444-444444444444";
const volumeUUID = "55555555-5555-4555-8555-555555555555";
const key = await crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"]);
const privateKey = Buffer.from(await crypto.subtle.exportKey("pkcs8", key.privateKey)).toString("base64");
const publicKey = Buffer.from(await crypto.subtle.exportKey("spki", key.publicKey)).toString("base64");

for (const outcome of ["success", "http-error", "network-error", "missing-upload", "start-error"]) {
  test(`moving a home through the Worker: ${outcome}`, async (t) => {
    const calls = [];
    let snapshotUUID;
    const { mf, DB, VOLUMES } = await createBindings(t, {
      script: bundle.outputFiles[0].text,
      bindings: {
        PWN_WORKSPACE_PRIVATE_KEY_B64: privateKey,
        PWN_WORKSPACE_PUBLIC_KEY_B64: publicKey,
        PWN_WORKSPACE_ORIGIN: "https://control.test",
        PWN_WORKSPACE_ENVIRONMENT: "development",
      },
      outboundService: async (request) => {
        const url = new URL(request.url);
        const action = url.pathname.split("/").at(-1);
        const text = await request.text();
        const body = text ? JSON.parse(text) : {};
        calls.push(`${url.hostname}/${action}`);
        if (url.hostname === "old.test") {
          assert.equal(action, "export");
          snapshotUUID = url.pathname.split("/").at(-2);
          assert.ok(body.stop_workspace_uuid);
          if (outcome !== "missing-upload") {
            const uploaded = await mf.dispatchFetch(body.upload_url, { method: "PUT", body: "home contents", headers: { "content-length": String(Buffer.byteLength("home contents")) } });
            assert.equal(uploaded.status, 200, await uploaded.text());
          }
          if (outcome === "network-error") throw new Error("node unavailable");
          if (outcome === "http-error") return new Response(null, { status: 409 });
        } else {
          assert.equal(url.hostname, "new.test");
          assert.equal(action, "start");
          assert.equal(body.volume.snapshot.snapshot_uuid, snapshotUUID);
          assert.equal(body.replace_workspace_uuid, undefined);
          const snapshot = await mf.dispatchFetch(body.volume.snapshot.download_url);
          if (outcome === "missing-upload") {
            assert.equal(snapshot.status, 404);
            return Response.json({ error: { code: "volume_prepare_failed", message: "Snapshot not found" } }, { status: 500 });
          }
          assert.equal(snapshot.status, 200);
          assert.equal(await snapshot.text(), "home contents");
          if (outcome === "start-error") return Response.json({ operation_started: false, error: { code: "image_not_available", message: "missing" } }, { status: 409 });
        }
        return new Response(null, { status: 200 });
      },
    });
    await DB.batch([
      DB.prepare("UPDATE nodes SET base_url = 'https://old.test' WHERE node_id = 1"),
      DB.prepare("UPDATE nodes SET base_url = 'https://new.test', status = 'active' WHERE node_id = 2"),
      DB.prepare("INSERT INTO volumes VALUES (1, ?, NULL, 1, 1073741824, 0)").bind(volumeUUID),
      DB.prepare("INSERT INTO user_home_volumes VALUES (1, 1)"),
      DB.prepare("INSERT INTO workspaces VALUES (1, ?, 1, 'test', '{}', 'running', 0, 0)").bind(crypto.randomUUID()),
      DB.prepare("INSERT INTO user_workspaces VALUES (1, 1)"),
    ]);
    const login = await mf.dispatchFetch("https://control.test/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ user_uuid: userUUID }),
    });
    assert.equal(login.status, 200);
    const response = await mf.dispatchFetch("https://control.test/api/workspaces/start", {
      method: "POST",
      headers: { "content-type": "application/json", cookie: login.headers.get("set-cookie").split(";")[0] },
      body: JSON.stringify({ node_uuid: targetNodeUUID, runtime_config: { container_image_ref: "test" } }),
    });
    assert.equal(response.status, 200);
    const events = (await response.text()).trim().split("\n").map((line) => decodeEvent(JSON.parse(line)));
    const error = events.find((event) => event.event === "error");
    const volume = await DB.prepare("SELECT node_id, snapshot_uuid FROM volumes WHERE volume_id = 1").first();
    const operation = await DB.prepare("SELECT operation_uuid, plan_json FROM workspace_operations").first();
    if (outcome === "success") {
      assert.equal(error, undefined, JSON.stringify(events));
      assert.ok(events.find((event) => event.event === "complete")?.workspace_uuid);
      assert.equal(operation, null);
      assert.deepEqual(volume, { node_id: 2, snapshot_uuid: snapshotUUID });
      assert.deepEqual(calls, ["old.test/export", "new.test/start"]);
      assert.equal(await (await VOLUMES.get(`snapshots/${volumeUUID}/${snapshotUUID}`)).text(), "home contents");
    } else {
      assert.ok(error, JSON.stringify(events));
      assert.equal(JSON.parse(operation.plan_json).snapshot_uuid, snapshotUUID);
      assert.deepEqual(volume, { node_id: 1, snapshot_uuid: null });
      assert.deepEqual(calls, ["start-error", "missing-upload"].includes(outcome) ? ["old.test/export", "new.test/start"] : ["old.test/export"]);
      const retry = await mf.dispatchFetch("https://control.test/api/workspaces/start", {
        method: "POST", headers: { "content-type": "application/json", cookie: login.headers.get("set-cookie").split(";")[0] },
        body: JSON.stringify({ node_uuid: targetNodeUUID, runtime_config: { container_image_ref: "test" } }),
      });
      assert.match(await retry.text(), /workspace_operation_in_progress/);
      assert.equal(calls.length, ["start-error", "missing-upload"].includes(outcome) ? 2 : 1, "blocked retry must not contact either node");
    }
  });
}
