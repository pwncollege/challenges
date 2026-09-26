import assert from "node:assert/strict";
import test from "node:test";
import { createBindings, loadModule, runEffect } from "./helpers.mjs";

import { Effect } from "effect";
const { WorkspaceStore, Environment } = await loadModule("tests/fixtures/services.ts");
const claimWorkspaceStart = (env, input) => runEffect(Effect.gen(function*() {
  const store = yield* WorkspaceStore.make;
  return yield* store.claimStart(input.userUUID, {
    node_uuid: input.nodeUUID, runtime_config: input.runtimeConfig,
  }, input.workspaceUuid);
}).pipe(Effect.provideService(Environment, env)));
const USER_UUID = "11111111-1111-4111-8111-111111111111";
const NODE_UUID = "33333333-3333-4333-8333-333333333333";

function request(nodeUUID = NODE_UUID) {
  return {
    userUUID: USER_UUID,
    nodeUUID,
    workspaceUuid: crypto.randomUUID(),
    runtimeConfig: { container_image_ref: "local-test-image" },
  };
}

async function locks(db) {
  return (await db.prepare("SELECT * FROM workspace_operations").all()).results;
}

test("a missing user leaves no workspace or volume behind", async (t) => {
  const env = await createBindings(t);
  await assert.rejects(
    () => claimWorkspaceStart(env, { ...request(), userUUID: crypto.randomUUID() }),
    { code: "user_not_found" },
  );
  assert.equal(await env.DB.prepare("SELECT COUNT(*) AS count FROM workspaces").first("count"), 0);
  assert.equal(await env.DB.prepare("SELECT COUNT(*) AS count FROM volumes").first("count"), 0);
  assert.deepEqual(await locks(env.DB), []);
});

for (const [name, nodeUUID] of [
  ["disabled", "44444444-4444-4444-8444-444444444444"],
  ["missing", "55555555-5555-4555-8555-555555555555"],
]) {
  test(`a rejected ${name} node preserves an existing workspace claim`, async (t) => {
    const env = await createBindings(t);
    const first = await claimWorkspaceStart(env, request());
    const heldLocks = await locks(env.DB);
    assert.equal(heldLocks.length, 1);

    await assert.rejects(() => claimWorkspaceStart(env, request(nodeUUID)), { code: "node_not_active" });
    assert.deepEqual(await locks(env.DB), heldLocks);
    await assert.rejects(() => claimWorkspaceStart(env, request()), { code: "workspace_operation_in_progress" });
    assert.equal(await env.DB.prepare("SELECT COUNT(*) AS count FROM workspaces").first("count"), 1);

    await runEffect(Effect.gen(function*() {
      const store = yield* WorkspaceStore.make;
      yield* store.failStart(first);
    }).pipe(Effect.provideService(Environment, env)));
    assert.deepEqual(await locks(env.DB), []);
    const next = await claimWorkspaceStart(env, request());
    assert.equal(next.homeVolume.volumeUuid, first.homeVolume.volumeUuid);
  });
}

const withStore = (env, f) => runEffect(Effect.flatMap(WorkspaceStore.make, f).pipe(Effect.provideService(Environment, env)));

test("stale start cleanup and completion cannot modify a newer operation", async (t) => {
  const env = await createBindings(t);
  const old = await claimWorkspaceStart(env, request());
  await withStore(env, (store) => store.failStart(old));
  const current = await claimWorkspaceStart(env, request());
  const before = await locks(env.DB);
  await withStore(env, (store) => store.failStart(old));
  await withStore(env, (store) => store.preserveSnapshot(old, current.homeVolume.volumeId, crypto.randomUUID()));
  await withStore(env, (store) => store.clearStoppedWorkspace(old, current.workspace.workspaceId));
  await assert.rejects(() => withStore(env, (store) => store.completeStart(old, old.homeVolume)),
    { code: "workspace_operation_conflict" });
  assert.deepEqual(await locks(env.DB), before);
  assert.equal(await env.DB.prepare("SELECT COUNT(*) FROM workspaces WHERE workspace_uuid = ?")
    .bind(current.workspace.workspaceUuid).first("COUNT(*)"), 1);
  assert.equal(await env.DB.prepare("SELECT snapshot_uuid FROM volumes").first("snapshot_uuid"), null);
  await withStore(env, (store) => store.completeStart(current, current.homeVolume));
  assert.deepEqual(await locks(env.DB), []);
});

test("start and stop share one claim, and stale stop callbacks cannot undo its successor", async (t) => {
  const env = await createBindings(t);
  const start = await claimWorkspaceStart(env, request());
  await assert.rejects(() => withStore(env, (store) => store.claimStop(USER_UUID)),
    { code: "workspace_operation_in_progress" });
  await withStore(env, (store) => store.completeStart(start, start.homeVolume));
  const old = await withStore(env, (store) => store.claimStop(USER_UUID));
  await assert.rejects(() => claimWorkspaceStart(env, request()), { code: "workspace_operation_in_progress" });
  await withStore(env, (store) => store.failStop(old));
  const current = await withStore(env, (store) => store.claimStop(USER_UUID));
  const before = await locks(env.DB);
  await withStore(env, (store) => store.failStop(old));
  await assert.rejects(() => withStore(env, (store) => store.completeStop(old)),
    { code: "workspace_operation_conflict" });
  assert.deepEqual(await locks(env.DB), before);
  assert.equal(await env.DB.prepare("SELECT status FROM workspaces").first("status"), "destroying");
  await withStore(env, (store) => store.completeStop(current));
  assert.deepEqual(await locks(env.DB), []);
  assert.equal(await env.DB.prepare("SELECT COUNT(*) FROM workspaces").first("COUNT(*)"), 0);
});
