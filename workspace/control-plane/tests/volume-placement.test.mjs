import assert from "node:assert/strict";
import test from "node:test";
import { build } from "esbuild";
import { createBindings } from "./helpers.mjs";

const bundle = await build({ entryPoints: ["src/index.ts"], bundle: true, format: "esm", write: false });
const userUUID = "11111111-1111-4111-8111-111111111111";
const targetNodeUUID = "44444444-4444-4444-8444-444444444444";
const volumeUUID = "55555555-5555-4555-8555-555555555555";
const key = await crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"]);
const privateKey = Buffer.from(await crypto.subtle.exportKey("pkcs8", key.privateKey)).toString("base64");
const publicKey = Buffer.from(await crypto.subtle.exportKey("spki", key.publicKey)).toString("base64");

for (const outcome of ["success", "http-error", "network-error", "missing-upload", "activation-error"]) {
  test(`moving a home through the Worker: ${outcome}`, async (t) => {
    const calls = [];
    let snapshotUUID;
    let stagingKey;
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
          if (action === "snapshot") snapshotUUID = body.snapshot_uuid;
          if (action === "upload") {
            const transfer = new URL(body.url);
            stagingKey = `staging/${volumeUUID}/${snapshotUUID}/${transfer.searchParams.get("upload_uuid")}`;
            if (outcome !== "missing-upload") {
              const uploaded = await mf.dispatchFetch(body.url, { method: "PUT", body: "home contents" });
              assert.equal(uploaded.status, 200, await uploaded.text());
            }
          }
          if (action === "deactivate") {
            assert.ok(await VOLUMES.head(`snapshots/${volumeUUID}/${snapshotUUID}`));
            if (outcome === "network-error") throw new Error("node unavailable");
            if (outcome === "http-error") return new Response(null, { status: 409 });
          }
        } else {
          assert.equal(url.hostname, "new.test");
          if (action === "download") {
            assert.equal(body.snapshot_uuid, snapshotUUID);
            const snapshot = await mf.dispatchFetch(body.url);
            assert.equal(snapshot.status, 200);
            assert.equal(await snapshot.text(), "home contents");
          }
          if (action === "activate") {
            assert.equal(body.snapshot_uuid, snapshotUUID);
            if (outcome === "activation-error") return new Response(null, { status: 500 });
          }
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
    const events = (await response.text()).trim().split("\n").map((line) => JSON.parse(line));
    const error = events.find((event) => event.event === "error");
    const volume = await DB.prepare("SELECT node_id, snapshot_uuid FROM volumes WHERE volume_id = 1").first();
    assert.equal(await DB.prepare("SELECT COUNT(*) AS count FROM user_workspace_locks").first("count"), 0);
    assert.equal(await DB.prepare("SELECT COUNT(*) AS count FROM volume_locks").first("count"), 0);

    if (outcome === "missing-upload") {
      assert.equal(error?.code, "volume_reclaim_failed");
      assert.deepEqual(calls, ["old.test/stop", "old.test/snapshot", "old.test/upload"]);
      assert.deepEqual(volume, { node_id: 1, snapshot_uuid: null });
      return;
    }
    const expectedCalls = [
      "old.test/stop", "old.test/snapshot", "old.test/upload", "old.test/deactivate",
      "new.test/download", "new.test/deactivate", "new.test/activate",
    ];
    if (outcome === "activation-error") {
      assert.equal(error?.code, "volume_activation_failed");
      assert.deepEqual(volume, { node_id: null, snapshot_uuid: snapshotUUID });
      assert.equal(await DB.prepare("SELECT COUNT(*) AS count FROM workspaces").first("count"), 0);
    } else {
      assert.equal(error, undefined, JSON.stringify(events));
      assert.ok(events.find((event) => event.event === "complete")?.workspace_uuid);
      assert.deepEqual(volume, { node_id: 2, snapshot_uuid: snapshotUUID });
      expectedCalls.push("new.test/start");
    }
    assert.deepEqual(calls, expectedCalls);
    assert.equal(await VOLUMES.head(stagingKey), null);
    assert.equal(await (await VOLUMES.get(`snapshots/${volumeUUID}/${snapshotUUID}`)).text(), "home contents");
  });
}
