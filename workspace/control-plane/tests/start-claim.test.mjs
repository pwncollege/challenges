import assert from "node:assert/strict";
import test from "node:test";
import { createBindings, loadModule } from "./helpers.mjs";

const { claimWorkspaceStart, failWorkspaceStart } = await loadModule("src/workspaces/start-claim.ts");
const USER_UUID = "11111111-1111-4111-8111-111111111111";
const NODE_UUID = "33333333-3333-4333-8333-333333333333";

function request(nodeUUID = NODE_UUID) {
  return {
    userUUID: USER_UUID,
    nodeUUID,
    newVolumeUUID: crypto.randomUUID(),
    workspaceUuid: crypto.randomUUID(),
    runtimeConfig: { container_image_ref: "local-test-image" },
    now: Math.floor(Date.now() / 1000),
  };
}

async function locks(db) {
  return {
    workspace: (await db.prepare("SELECT * FROM user_workspace_locks").all()).results,
    volume: (await db.prepare("SELECT * FROM volume_locks").all()).results,
  };
}

test("a missing user leaves no workspace or volume behind", async (t) => {
  const env = await createBindings(t);
  await assert.rejects(
    () => claimWorkspaceStart(env, { ...request(), userUUID: crypto.randomUUID() }),
    { code: "user_not_found" },
  );
  assert.equal(await env.DB.prepare("SELECT COUNT(*) AS count FROM workspaces").first("count"), 0);
  assert.equal(await env.DB.prepare("SELECT COUNT(*) AS count FROM volumes").first("count"), 0);
  assert.deepEqual(await locks(env.DB), { workspace: [], volume: [] });
});

for (const [name, nodeUUID] of [
  ["disabled", "44444444-4444-4444-8444-444444444444"],
  ["missing", "55555555-5555-4555-8555-555555555555"],
]) {
  test(`a rejected ${name} node preserves an existing workspace claim`, async (t) => {
    const env = await createBindings(t);
    const first = await claimWorkspaceStart(env, request());
    const heldLocks = await locks(env.DB);
    assert.equal(heldLocks.workspace.length, 1);
    assert.equal(heldLocks.volume.length, 1);

    await assert.rejects(() => claimWorkspaceStart(env, request(nodeUUID)), { code: "node_not_active" });
    assert.deepEqual(await locks(env.DB), heldLocks);
    await assert.rejects(() => claimWorkspaceStart(env, request()), { code: "workspace_start_locked" });
    assert.equal(await env.DB.prepare("SELECT COUNT(*) AS count FROM workspaces").first("count"), 1);

    await failWorkspaceStart(env, first.userId, first.workspace.workspaceId, first.homeVolume.volumeId);
    assert.deepEqual(await locks(env.DB), { workspace: [], volume: [] });
    const next = await claimWorkspaceStart(env, request());
    assert.equal(next.homeVolume.volumeUuid, first.homeVolume.volumeUuid);
  });
}
