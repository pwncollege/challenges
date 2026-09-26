import type { Bindings } from "../common.ts";
import { rows } from "../common.ts";
import { workspaceError } from "./errors.ts";
import type { ClaimedWorkspaceStart, ClaimWorkspaceStartInput, WorkspaceStatus } from "./types.ts";

const DEFAULT_HOME_VOLUME_SIZE_BYTES = 1024 * 1024 * 1024;

type UserRow = { user_id: number };
type WorkspaceInsertRow = { workspace_id: number };
type ExistingWorkspaceRow = {
  workspace_id: number;
  workspace_uuid: string;
  status: WorkspaceStatus;
  node_id: number;
  node_uuid: string;
  node_base_url: string;
};
type HomeVolumeRow = {
  volume_id: number;
  volume_uuid: string;
  snapshot_uuid: string | null;
  node_id: number | null;
  node_uuid: string | null;
  node_base_url: string | null;
};
type TargetNodeRow = {
  node_id: number;
  node_uuid: string;
  base_url: string;
};
type ClaimRows = {
  userWorkspaceLockChanges: number;
  volumeLockChanges: number;
  userRows: UserRow[];
  workspaceRows: WorkspaceInsertRow[];
  existingWorkspaceRows: ExistingWorkspaceRow[];
  homeVolumeRows: HomeVolumeRow[];
  targetNodeRows: TargetNodeRow[];
};

function expectChanges(result: D1Result<unknown>, expected: number, code = "database_conflict") {
  if (result.meta.changes !== expected) {
    throw workspaceError(code, code);
  }
}

async function cleanupFailedWorkspaceStartClaim(env: Bindings, userId: number, workspaceUuid: string) {
  await env.DB.batch([
    env.DB.prepare(
      `DELETE FROM volume_locks
       WHERE volume_id IN (
         SELECT volume_id
         FROM user_home_volumes
         WHERE user_id = ?
       )`,
    ).bind(userId),
    env.DB.prepare("DELETE FROM user_workspace_locks WHERE user_id = ?").bind(userId),
    env.DB.prepare("DELETE FROM workspaces WHERE workspace_uuid = ? AND status = 'creating'").bind(workspaceUuid),
  ]).catch(() => undefined);
}

export async function failWorkspaceStart(env: Bindings, userId: number, workspaceId: number, volumeId: number) {
  await env.DB.batch([
    env.DB.prepare("DELETE FROM volume_locks WHERE volume_id = ?").bind(volumeId),
    env.DB.prepare("DELETE FROM user_workspace_locks WHERE user_id = ?").bind(userId),
    env.DB.prepare("DELETE FROM workspaces WHERE workspace_id = ? AND status = 'creating'").bind(workspaceId),
  ]).catch(() => undefined);
}

export async function completeWorkspaceStart(
  env: Bindings,
  input: {
    userId: number;
    workspaceId: number;
    oldWorkspaceId: number | null;
    volumeId: number;
    targetNodeId: number;
    snapshotUuid: string | null;
    now: number;
  },
) {
  const statements = [
    env.DB.prepare("UPDATE volumes SET node_id = ?, snapshot_uuid = ?, updated_at = ? WHERE volume_id = ?").bind(
      input.targetNodeId,
      input.snapshotUuid,
      input.now,
      input.volumeId,
    ),
    env.DB.prepare(
      `INSERT INTO user_workspaces (user_id, workspace_id)
       VALUES (?, ?)
       ON CONFLICT(user_id) DO UPDATE SET workspace_id = excluded.workspace_id`,
    ).bind(input.userId, input.workspaceId),
    env.DB.prepare("UPDATE workspaces SET status = 'running', updated_at = ? WHERE workspace_id = ?").bind(
      input.now,
      input.workspaceId,
    ),
    env.DB.prepare("DELETE FROM volume_locks WHERE volume_id = ?").bind(input.volumeId),
    env.DB.prepare("DELETE FROM user_workspace_locks WHERE user_id = ?").bind(input.userId),
  ];
  if (input.oldWorkspaceId !== null) {
    statements.push(env.DB.prepare("DELETE FROM workspaces WHERE workspace_id = ?").bind(input.oldWorkspaceId));
  }
  const results = await env.DB.batch(statements);
  expectChanges(results[0], 1, "volume_update_failed");
  expectChanges(results[1], 1, "user_workspace_update_failed");
  expectChanges(results[2], 1, "workspace_update_failed");
  expectChanges(results[3], 1, "volume_lock_release_failed");
  expectChanges(results[4], 1, "workspace_lock_release_failed");
  if (input.oldWorkspaceId !== null) {
    expectChanges(results[5], 1, "old_workspace_delete_failed");
  }
}

export async function claimWorkspaceStart(env: Bindings, input: ClaimWorkspaceStartInput): Promise<ClaimedWorkspaceStart> {
  const claimRows = parseClaimRows(await runClaimBatch(env, input));
  if (claimRows.userRows.length === 0) {
    throw workspaceError("user_not_found", "User not found", 404);
  }
  if (claimRows.targetNodeRows.length === 0) {
    throw workspaceError("node_not_active", "Node is not active", 409);
  }
  if (!validClaimRows(claimRows)) {
    await cleanupFailedWorkspaceStartClaim(env, claimRows.userRows[0].user_id, input.workspaceUuid);
    throw workspaceError("workspace_start_claim_failed");
  }
  return mapClaimRows(input, claimRows);
}

async function runClaimBatch(env: Bindings, input: ClaimWorkspaceStartInput) {
  const runtimeConfigJSON = JSON.stringify(input.runtimeConfig);
  try {
    return await env.DB.batch([
      env.DB.prepare(
        `INSERT INTO user_workspace_locks (user_id, locked_at)
         SELECT u.user_id, ?
         FROM users u
         WHERE u.user_uuid = ?
           AND EXISTS (
             SELECT 1
             FROM nodes n
             WHERE n.node_uuid = ?
               AND n.status = 'active'
           )`,
      ).bind(input.now, input.userUUID, input.nodeUUID),
      env.DB.prepare(
        `INSERT INTO volumes (volume_uuid, snapshot_uuid, node_id, max_size_bytes, updated_at)
         SELECT ?, NULL, NULL, ?, ?
         WHERE EXISTS (SELECT 1 FROM users u WHERE u.user_uuid = ?)
           AND EXISTS (
             SELECT 1
             FROM nodes n
             WHERE n.node_uuid = ?
               AND n.status = 'active'
           )
           AND NOT EXISTS (
             SELECT 1
             FROM user_home_volumes uv
             JOIN users u
               ON u.user_id = uv.user_id
             WHERE u.user_uuid = ?
           )`,
      ).bind(
        input.newVolumeUUID,
        DEFAULT_HOME_VOLUME_SIZE_BYTES,
        input.now,
        input.userUUID,
        input.nodeUUID,
        input.userUUID,
      ),
      env.DB.prepare(
        `INSERT INTO user_home_volumes (user_id, volume_id)
         SELECT u.user_id, v.volume_id
         FROM users u
         JOIN volumes v
           ON v.volume_uuid = ?
         WHERE u.user_uuid = ?
           AND NOT EXISTS (
             SELECT 1
             FROM user_home_volumes existing
             WHERE existing.user_id = u.user_id
           )`,
      ).bind(input.newVolumeUUID, input.userUUID),
      env.DB.prepare(
        `INSERT INTO volume_locks (volume_id, locked_at)
         SELECT uv.volume_id, ?
         FROM user_home_volumes uv
         JOIN users u
           ON u.user_id = uv.user_id
         WHERE u.user_uuid = ?
           AND EXISTS (
             SELECT 1
             FROM nodes n
             WHERE n.node_uuid = ?
               AND n.status = 'active'
           )`,
      ).bind(input.now, input.userUUID, input.nodeUUID),
      env.DB.prepare(
        `INSERT INTO workspaces (
           workspace_uuid,
           node_id,
           container_image_ref,
           runtime_config_json,
           status,
           created_at,
           updated_at
         )
         SELECT ?, n.node_id, ?, ?, 'creating', ?, ?
         FROM nodes n
         WHERE n.node_uuid = ?
           AND n.status = 'active'
           AND EXISTS (SELECT 1 FROM users u WHERE u.user_uuid = ?)
         RETURNING workspace_id`,
      ).bind(
        input.workspaceUuid,
        input.runtimeConfig.container_image_ref,
        runtimeConfigJSON,
        input.now,
        input.now,
        input.nodeUUID,
        input.userUUID,
      ),
      env.DB.prepare("SELECT user_id FROM users WHERE user_uuid = ?").bind(input.userUUID),
      env.DB.prepare(
        `SELECT
           ws.workspace_id,
           ws.workspace_uuid,
           ws.status,
           ws.node_id,
           n.node_uuid,
           n.base_url AS node_base_url
         FROM user_workspaces uw
         JOIN users u
           ON u.user_id = uw.user_id
         JOIN workspaces ws
           ON ws.workspace_id = uw.workspace_id
         JOIN nodes n
           ON n.node_id = ws.node_id
         WHERE u.user_uuid = ?`,
      ).bind(input.userUUID),
      env.DB.prepare(
        `SELECT
           v.volume_id,
           v.volume_uuid,
           v.snapshot_uuid,
           v.node_id,
           n.node_uuid,
           n.base_url AS node_base_url
         FROM user_home_volumes uv
         JOIN users u
           ON u.user_id = uv.user_id
         JOIN volumes v
           ON v.volume_id = uv.volume_id
         LEFT JOIN nodes n
           ON n.node_id = v.node_id
         WHERE u.user_uuid = ?`,
      ).bind(input.userUUID),
      env.DB.prepare(
        `SELECT
           node_id,
           node_uuid,
           base_url
         FROM nodes
         WHERE node_uuid = ?
           AND status = 'active'`,
      ).bind(input.nodeUUID),
    ]);
  } catch (error) {
    throw workspaceError("workspace_start_locked", "workspace_start_locked", 409, error);
  }
}

function parseClaimRows(results: D1Result<unknown>[]): ClaimRows {
  return {
    userWorkspaceLockChanges: results[0].meta.changes,
    volumeLockChanges: results[3].meta.changes,
    workspaceRows: rows<WorkspaceInsertRow>(results[4]),
    userRows: rows<UserRow>(results[5]),
    existingWorkspaceRows: rows<ExistingWorkspaceRow>(results[6]),
    homeVolumeRows: rows<HomeVolumeRow>(results[7]),
    targetNodeRows: rows<TargetNodeRow>(results[8]),
  };
}

function validClaimRows(claimRows: ClaimRows) {
  return (
    claimRows.userWorkspaceLockChanges === 1 &&
    claimRows.volumeLockChanges === 1 &&
    claimRows.workspaceRows.length === 1 &&
    claimRows.existingWorkspaceRows.length <= 1 &&
    claimRows.homeVolumeRows.length === 1 &&
    claimRows.targetNodeRows.length === 1
  );
}

function mapClaimRows(input: ClaimWorkspaceStartInput, claimRows: ClaimRows): ClaimedWorkspaceStart {
  const existingWorkspace = claimRows.existingWorkspaceRows[0];
  const homeVolume = claimRows.homeVolumeRows[0];
  const targetNode = claimRows.targetNodeRows[0];
  const authoritativeNode = homeVolume.node_id === null
    ? null
    : {
        nodeId: homeVolume.node_id,
        nodeUUID: homeVolume.node_uuid ?? "",
        baseUrl: homeVolume.node_base_url ?? "",
      };

  if (homeVolume.node_id !== null && (!homeVolume.node_uuid || !homeVolume.node_base_url)) {
    throw workspaceError("workspace_start_claim_failed");
  }

  return {
    userId: claimRows.userRows[0].user_id,
    workspace: {
      workspaceId: claimRows.workspaceRows[0].workspace_id,
      workspaceUuid: input.workspaceUuid,
    },
    targetNode: {
      nodeId: targetNode.node_id,
      nodeUUID: targetNode.node_uuid,
      baseUrl: targetNode.base_url,
    },
    existingWorkspace: existingWorkspace
      ? {
          workspaceId: existingWorkspace.workspace_id,
          workspaceUuid: existingWorkspace.workspace_uuid,
          status: existingWorkspace.status,
          node: {
            nodeId: existingWorkspace.node_id,
            nodeUUID: existingWorkspace.node_uuid,
            baseUrl: existingWorkspace.node_base_url,
          },
        }
      : null,
    homeVolume: {
      volumeId: homeVolume.volume_id,
      volumeUuid: homeVolume.volume_uuid,
      snapshotUuid: homeVolume.snapshot_uuid,
      authoritativeNode,
    },
  };
}
