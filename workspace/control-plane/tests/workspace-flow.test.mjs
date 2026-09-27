import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import test, { after, before } from "node:test";
import { build } from "esbuild";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";
import { unstable_getMiniflareWorkerOptions } from "wrangler";
import { Effect } from "effect";
import { loadModule, runEffect } from "./helpers.mjs";

const CONTROL = "http://127.0.0.1:8787";
const DAEMON = process.env.PWN_WORKSPACE_DAEMON_URL ?? "http://127.0.0.1:8000";
const SECONDARY_DAEMON = process.env.PWN_WORKSPACE_SECONDARY_DAEMON_URL;
const USER_UUID = "11111111-1111-4111-8111-111111111111";
const NODE_UUID = "33333333-3333-4333-8333-333333333333";
const DISABLED_NODE_UUID = "44444444-4444-4444-8444-444444444444";
const IMAGE = "docker.io/library/alpine:3.22";

let mf;
let db;
let sessionCookie;
let currentWorkspaceURL;

async function execSQLFile(path) {
  const sql = await fs.readFile(path, "utf8");
  for (const statement of sql.split(";")) {
    const normalized = statement.replace(/\s+/g, " ").trim();
    if (normalized !== "") await db.exec(`${normalized};`);
  }
}

async function daemonFetch(path, options) {
  return fetch(new URL(path, DAEMON), options);
}

async function pullTestImage() {
  const response = await daemonFetch("/api/container_images/pull", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ container_image_ref: IMAGE }),
  });
  const result = await response.json();
  assert.equal(response.status, 200, JSON.stringify(result));
  assert.equal(result.container_image_ref, IMAGE);
  assert.equal(result.pulled, true);
}

async function login(userUuid = USER_UUID) {
  const response = await fetch(`${CONTROL}/api/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ user_uuid: userUuid }),
  });
  return {
    response,
    json: await response.json(),
    cookie: response.headers.get("set-cookie")?.split(";")[0],
  };
}

async function startWorkspace(overrides = {}) {
  const response = await fetch(`${CONTROL}/api/workspaces/start`, {
    method: "POST",
    headers: { "content-type": "application/json", cookie: sessionCookie },
    body: JSON.stringify({
      node_uuid: NODE_UUID,
      volume_dst_path: "/home/hacker",
      runtime_config: {
        container_image_ref: IMAGE,
        entrypoint: ["/bin/sh", "-lc", "printf initialized > /home/hacker/init.txt"],
        env: { E2E_VALUE: "present" },
      },
      ...overrides,
    }),
  });
  if (response.headers.get("content-type")?.includes("application/json")) {
    return { response, json: await response.json() };
  }
  const events = (await response.text()).trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
  const result = {
    response,
    events,
    complete: events.find((item) => item.event === "complete"),
    error: events.find((item) => item.event === "error"),
  };
  if (result.complete) currentWorkspaceURL = result.complete.url;
  return result;
}

async function stopWorkspace() {
  const response = await fetch(`${CONTROL}/api/workspaces/stop`, {
    method: "POST",
    headers: { cookie: sessionCookie },
  });
  if (response.ok) currentWorkspaceURL = undefined;
  return response;
}

async function execWorkspace(url, argv) {
  const response = await fetch(new URL("exec/", url), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ argv }),
  });
  assert.equal(response.status, 200);
  return response.json();
}

async function homeVolume() {
  const result = await db.prepare(
    `SELECT v.volume_uuid, v.node_id, v.snapshot_uuid
     FROM user_home_volumes uv
     JOIN volumes v ON v.volume_id = uv.volume_id
     WHERE uv.user_id = 1`,
  ).first();
  return result;
}

before(async () => {
  const health = await daemonFetch("/api/health");
  assert.equal(health.status, 200, "the workspace daemon must be running");
  assert.equal((await health.json()).volume_storage_enabled, true, "the daemon must have volume storage enabled");
  await pullTestImage();

  await fs.rm(".local/test", { force: true, recursive: true });
  await fs.mkdir(".local/test", { recursive: true });
  await build({
    bundle: true,
    entryPoints: ["src/index.ts"],
    format: "esm",
    outfile: ".local/test/index.js",
    platform: "browser",
    target: "es2022",
  });

  const { workerOptions } = await unstable_getMiniflareWorkerOptions("wrangler.toml");
  mf = new Miniflare(convertV4MiniflareOptions({
    ...workerOptions,
    // The test entry point is already bundled by esbuild.
    modulesRules: undefined,
    scriptPath: ".local/test/index.js",
    modules: true,
    host: "127.0.0.1",
    port: 8787,
    d1Persist: false,
    r2Persist: false,
    logRequests: false,
  }));
  await mf.ready;
  db = await mf.getD1Database("DB");
  await execSQLFile("migrations/0001_schema.sql");
  await execSQLFile("seed.sql");
  await db.prepare("UPDATE nodes SET base_url = ? WHERE node_uuid = ?").bind(DAEMON, NODE_UUID).run();
  const loggedIn = await login();
  assert.equal(loggedIn.response.status, 200);
  sessionCookie = loggedIn.cookie;
});

after(async () => {
  if (currentWorkspaceURL && sessionCookie) await stopWorkspace().catch(() => undefined);
  if (db) {
    const volume = await homeVolume().catch(() => undefined);
    if (volume?.volume_uuid) {
      await daemonFetch(`/api/volumes/${volume.volume_uuid}/delete`, { method: "POST" }).catch(() => undefined);
      if (SECONDARY_DAEMON) {
        await fetch(`${SECONDARY_DAEMON}/api/volumes/${volume.volume_uuid}/delete`, { method: "POST" }).catch(() => undefined);
      }
    }
  }
  await mf?.dispose();
  await fs.rm(".local/test", { force: true, recursive: true });
});

test("login, node listing, and request validation", async () => {
  const missingLogin = await login("99999999-9999-4999-8999-999999999999");
  assert.equal(missingLogin.response.status, 404);
  assert.equal(missingLogin.json.error.code, "user_not_found");

  const unauthorized = await fetch(`${CONTROL}/api/workspaces/start`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({}),
  });
  assert.equal(unauthorized.status, 401);

  const nodes = await fetch(`${CONTROL}/api/nodes`, { headers: { cookie: sessionCookie } });
  assert.equal(nodes.status, 200);
  assert.deepEqual(await nodes.json(), {
    nodes: [{ node_uuid: NODE_UUID, base_url: DAEMON }],
    current_home_node: null,
  });

  const invalidPath = await startWorkspace({ volume_dst_path: "/" });
  assert.equal(invalidPath.response.status, 400);
  assert.equal(invalidPath.json.error.code, "invalid_request");

  const disabledNode = await startWorkspace({ node_uuid: DISABLED_NODE_UUID });
  assert.equal(disabledNode.response.status, 200);
  assert.equal(disabledNode.error.code, "node_not_active");
});

test("a failed daemon start releases the control-plane claim", async () => {
  const result = await startWorkspace({
    runtime_config: { container_image_ref: "missing-local-image:e2e" },
  });
  assert.equal(result.response.status, 200);
  assert.equal(result.error.code, "image_not_available");

  const workspaceCount = await db.prepare(
    "SELECT COUNT(*) AS count FROM user_workspaces WHERE user_id = 1",
  ).first("count");
  const lockCount = await db.prepare(
    "SELECT COUNT(*) AS count FROM workspace_operations WHERE user_id = 1",
  ).first("count");
  assert.equal(workspaceCount, 0);
  assert.equal(lockCount, 0);
});

test("start, proxy, replace, stop, and restart preserve the home volume", async () => {
  const first = await startWorkspace();
  assert.equal(first.response.status, 200);
  assert.ok(first.complete?.workspace_uuid, JSON.stringify(first.error ?? first.events));
  assert.equal(first.complete.url, `${DAEMON}/w/${first.complete.workspace_uuid}/`);

  let executed = await execWorkspace(first.complete.url, [
    "/bin/sh",
    "-lc",
    "printf '%s:%s' \"$(cat /home/hacker/init.txt)\" \"$E2E_VALUE\"",
  ]);
  assert.deepEqual(executed, {
    exit_code: 0,
    stdout: "initialized:present",
    stderr: "",
  });

  const filesystem = await execWorkspace(first.complete.url, ["/bin/sh", "-c",
    "awk '$2 == \"/home/hacker\" { print $1, $3, $4 }' /proc/mounts; stat -c '%u:%g' /home/hacker"]);
  assert.equal(filesystem.exit_code, 0);
  assert.match(filesystem.stdout, /\/dev\/\S+ ext4 /);
  assert.match(filesystem.stdout, /nosuid/);
  assert.match(filesystem.stdout, /nodev/);
  assert.match(filesystem.stdout, /1000:1000/);
  const home = await homeVolume();
  const runtimeConfig = JSON.parse(await db.prepare("SELECT runtime_config_json FROM workspaces WHERE workspace_uuid = ?")
    .bind(first.complete.workspace_uuid).first("runtime_config_json"));
  const command = (path, body) => daemonFetch(path, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  });
  assert.deepEqual(await execWorkspace(first.complete.url, [
    "/bin/sh", "-c", "rm /home/hacker/init.txt && printf retry-marker > /home/hacker/init.txt",
  ]), { exit_code: 0, stdout: "", stderr: "" });
  const startPath = `/api/workspaces/${first.complete.workspace_uuid}/start`;
  const nodeBody = { runtime_config: runtimeConfig, volume: { volume_uuid: home.volume_uuid, dst_path: "/home/hacker", max_size_bytes: 1073741824, snapshot: null } };
  assert.equal((await command(startPath, nodeBody)).status, 200);
  assert.equal((await execWorkspace(first.complete.url, ["cat", "/home/hacker/init.txt"])).stdout, "retry-marker");
  assert.equal((await command(startPath, { ...nodeBody, runtime_config: { container_image_ref: IMAGE } })).status, 409);
  assert.deepEqual(await execWorkspace(first.complete.url, ["/bin/sh", "-c", "printf initialized > /home/hacker/init.txt"]),
    { exit_code: 0, stdout: "", stderr: "" });

  const replacement = await startWorkspace({
    runtime_config: {
      container_image_ref: IMAGE,
      entrypoint: [
        "/bin/sh",
        "-lc",
        "test \"$(cat /home/hacker/init.txt)\" = initialized && printf replaced > /home/hacker/init.txt",
      ],
    },
  });
  assert.equal(replacement.response.status, 200);
  assert.ok(replacement.complete?.workspace_uuid, JSON.stringify(replacement.error ?? replacement.events));
  assert.notEqual(replacement.complete.workspace_uuid, first.complete.workspace_uuid);

  assert.equal((await command(startPath, nodeBody)).status, 409, "a delayed start must not resurrect the stopped workspace");

  executed = await execWorkspace(replacement.complete.url, ["cat", "/home/hacker/init.txt"]);
  assert.equal(executed.exit_code, 0);
  assert.equal(executed.stdout, "replaced");

  const stopped = await stopWorkspace();
  assert.equal(stopped.status, 200);
  const volume = await homeVolume();
  assert.equal(volume.node_id, 1);
  assert.equal(volume.snapshot_uuid, null);

  const nodes = await fetch(`${CONTROL}/api/nodes`, { headers: { cookie: sessionCookie } });
  assert.deepEqual((await nodes.json()).current_home_node, {
    node_uuid: NODE_UUID,
    base_url: DAEMON,
  });

  const restarted = await startWorkspace({
    runtime_config: { container_image_ref: IMAGE },
  });
  assert.equal(restarted.response.status, 200);
  assert.ok(restarted.complete?.workspace_uuid, JSON.stringify(restarted.error ?? restarted.events));
  executed = await execWorkspace(restarted.complete.url, ["cat", "/home/hacker/init.txt"]);
  assert.equal(executed.exit_code, 0);
  assert.equal(executed.stdout, "replaced");

  const images = await daemonFetch("/api/container_images/list");
  assert.equal(images.status, 200);
  assert.ok((await images.json()).images.some((image) => image.repo_tags?.includes(IMAGE)));

  assert.equal((await stopWorkspace()).status, 200);
});

test("read-only EROFS, nested KVM, and CNI egress work inside Kata", async () => {
  const started = await startWorkspace();
  assert.ok(started.complete, JSON.stringify(started.error ?? started.events));
  for (const fixture of ["runtime-storage.py", "nested-kvm.py", "egress.py"]) {
    const script = await fs.readFile(new URL(`./fixtures/${fixture}`, import.meta.url), "utf8");
    const executed = await execWorkspace(started.complete.url, ["python3", "-c", script]);
    assert.equal(executed.exit_code, 0, `${fixture}: ${executed.stderr}`);
  }
  assert.equal((await stopWorkspace()).status, 200);
});

test("workspaces share the runtime disk across overlapping lifetimes", async () => {
  const first = await startWorkspace();
  assert.ok(first.complete, JSON.stringify(first.error ?? first.events));
  const secondUUID = randomUUID();
  const script = await fs.readFile(new URL("./fixtures/runtime-storage.py", import.meta.url), "utf8");
  try {
    const second = await daemonFetch(`/api/workspaces/${secondUUID}/start`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ runtime_config: { container_image_ref: IMAGE } }),
    });
    assert.equal(second.status, 200, await second.text());
    for (const url of [first.complete.url, `${DAEMON}/w/${secondUUID}/`]) {
      const result = await execWorkspace(url, ["python3", "-c", script]);
      assert.equal(result.exit_code, 0, result.stderr);
    }
  } finally {
    const stopped = await daemonFetch(`/api/workspaces/${secondUUID}/stop`, { method: "POST" });
    assert.equal(stopped.status, 200, await stopped.text());
  }
  const remaining = await execWorkspace(first.complete.url, ["python3", "-c", script]);
  assert.equal(remaining.exit_code, 0, remaining.stderr);
  assert.equal((await stopWorkspace()).status, 200);
});

test("moving the home between two daemons preserves its contents", { skip: !SECONDARY_DAEMON }, async () => {
  const health = await fetch(`${SECONDARY_DAEMON}/api/health`);
  assert.equal(health.status, 200);
  assert.equal((await health.json()).volume_storage_enabled, true);
  const pull = await fetch(`${SECONDARY_DAEMON}/api/container_images/pull`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ container_image_ref: IMAGE }),
  });
  assert.equal(pull.status, 200, await pull.text());
  await db.prepare("UPDATE nodes SET base_url = ?, status = 'active' WHERE node_uuid = ?")
    .bind(SECONDARY_DAEMON, DISABLED_NODE_UUID).run();

  const first = await startWorkspace();
  assert.ok(first.complete, JSON.stringify(first.error ?? first.events));
  let expected = "initialized";
  let firstSnapshot;
  for (const [nodeUUID, daemon, nodeId] of [
    [DISABLED_NODE_UUID, SECONDARY_DAEMON, 2],
    [NODE_UUID, DAEMON, 1],
  ]) {
    const moved = await startWorkspace({
      node_uuid: nodeUUID,
      runtime_config: { container_image_ref: IMAGE },
    });
    assert.ok(moved.complete, JSON.stringify(moved.error ?? moved.events));
    assert.equal(moved.complete.url, `${daemon}/w/${moved.complete.workspace_uuid}/`);
    const executed = await execWorkspace(moved.complete.url, ["cat", "/home/hacker/init.txt"]);
    assert.equal(executed.exit_code, 0);
    assert.equal(executed.stdout, expected);
    expected = `written-on-node-${nodeId}`;
    assert.equal((await execWorkspace(moved.complete.url, ["/bin/sh", "-c", `printf %s ${expected} > /home/hacker/init.txt`])).exit_code, 0);
    const volume = await homeVolume();
    assert.equal(volume.node_id, nodeId);
    assert.ok(volume.snapshot_uuid);
    firstSnapshot ??= volume.snapshot_uuid;
    const replay = await fetch(`${daemon}/api/workspaces/${moved.complete.workspace_uuid}/start`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ runtime_config: { container_image_ref: IMAGE }, volume: {
        volume_uuid: volume.volume_uuid, dst_path: "/home/hacker", max_size_bytes: 1073741824,
        snapshot: { snapshot_uuid: volume.snapshot_uuid, download_url: "https://refreshed.example/unused" },
      } }),
    });
    assert.equal(replay.status, 200, await replay.text());
  }
  const volume = await homeVolume();
  const delayedExport = await daemonFetch(`/api/volumes/${volume.volume_uuid}/snapshots/${firstSnapshot}/export`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ stop_workspace_uuid: first.complete.workspace_uuid, upload_url: "http://127.0.0.1:1/unavailable" }),
  });
  assert.equal(delayedExport.status, 500);
  const { snapshotUrl, Environment } = await loadModule("tests/fixtures/services.ts");
  const bindings = await mf.getBindings();
  const bucket = await mf.getR2Bucket("VOLUMES");
  const key = `snapshots/${volume.volume_uuid}/${firstSnapshot}`;
  const original = await (await bucket.get(key)).arrayBuffer();
  const retriedExport = await daemonFetch(`/api/volumes/${volume.volume_uuid}/snapshots/${firstSnapshot}/export`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({
      stop_workspace_uuid: first.complete.workspace_uuid,
      upload_url: await runEffect(snapshotUrl("PUT", volume.volume_uuid, firstSnapshot).pipe(Effect.provideService(Environment, bindings))),
    }),
  });
  assert.equal(retriedExport.status, 200, await retriedExport.text());
  assert.deepEqual(await (await bucket.get(key)).arrayBuffer(), original, "retry must recompress the retired image");
  assert.equal((await execWorkspace(currentWorkspaceURL, ["cat", "/home/hacker/init.txt"])).stdout, expected);
  assert.equal((await stopWorkspace()).status, 200);
});
