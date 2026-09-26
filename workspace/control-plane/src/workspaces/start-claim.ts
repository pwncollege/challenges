import { rows } from "../common.ts";
import { expectChanges, owned, ownsOperation, releaseOperation, type OperationClaim } from "./operations.ts";
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
  max_size_bytes: number;
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
  operationChanges: number;
  userRows: UserRow[];
  workspaceRows: WorkspaceInsertRow[];
  existingWorkspaceRows: ExistingWorkspaceRow[];
  homeVolumeRows: HomeVolumeRow[];
  targetNodeRows: TargetNodeRow[];
};

export async function failWorkspaceStart(db: D1Database, claim: OperationClaim, workspaceUuid: string) {
  await db.batch([
    owned(db, claim, `DELETE FROM workspaces WHERE workspace_uuid = ? AND status = 'creating' AND ${ownsOperation}`, workspaceUuid),
    releaseOperation(db, claim),
  ]);
}

export async function completeWorkspaceStart(
  db: D1Database,
  input: OperationClaim & {
    workspaceId: number;
    oldWorkspaceId: number | null;
    volumeId: number;
    targetNodeId: number;
    snapshotUuid: string | null;
    now: number;
  },
) {
  const statements = [
    owned(db, input, `UPDATE volumes SET node_id = ?, snapshot_uuid = ?, updated_at = ? WHERE volume_id = ? AND ${ownsOperation}`,
      input.targetNodeId, input.snapshotUuid, input.now, input.volumeId),
    owned(db, input, `INSERT INTO user_workspaces (user_id, workspace_id)
      SELECT ?, ? WHERE ${ownsOperation}
      ON CONFLICT(user_id) DO UPDATE SET workspace_id = excluded.workspace_id`, input.userId, input.workspaceId),
    owned(db, input, `UPDATE workspaces SET status = 'running', updated_at = ? WHERE workspace_id = ? AND ${ownsOperation}`,
      input.now, input.workspaceId),
  ];
  if (input.oldWorkspaceId !== null) {
    statements.push(owned(db, input, `DELETE FROM workspaces WHERE workspace_id = ? AND ${ownsOperation}`, input.oldWorkspaceId));
  }
  // Release last: every mutation in this atomic batch must still own the operation.
  statements.push(releaseOperation(db, input));
  const results = await db.batch(statements);
  for (const result of results) expectChanges(result);
}

export async function claimWorkspaceStart(db: D1Database, input: ClaimWorkspaceStartInput): Promise<ClaimedWorkspaceStart> {
  input = { ...input, exportSnapshotUuid: input.exportSnapshotUuid ?? crypto.randomUUID() };
  const claimRows = parseClaimRows(await runClaimBatch(db, input));
  if (claimRows.userRows.length === 0) {
    throw workspaceError("user_not_found", "User not found", 404);
  }
  if (claimRows.targetNodeRows.length === 0) {
    throw workspaceError("node_not_active", "Node is not active", 409);
  }
  if (!validClaimRows(claimRows)) {
    await failWorkspaceStart(db, { userId: claimRows.userRows[0].user_id, operationUuid: input.workspaceUuid }, input.workspaceUuid);
    throw workspaceError("workspace_start_claim_failed");
  }
  return mapClaimRows(input, claimRows);
}

async function runClaimBatch(db: D1Database, input: ClaimWorkspaceStartInput) {
  const runtimeConfigJSON = JSON.stringify(input.runtimeConfig);
  try {
    return await db.batch([
      db.prepare(
        `INSERT INTO workspace_operations (user_id, operation_uuid, kind, created_at, plan_json)
         SELECT u.user_id, ?, 'start', ?, ?
         FROM users u
         WHERE u.user_uuid = ?
           AND EXISTS (
             SELECT 1
             FROM nodes n
             WHERE n.node_uuid = ?
               AND n.status = 'active'
           )`,
      ).bind(input.workspaceUuid, input.now, JSON.stringify({ snapshot_uuid: input.exportSnapshotUuid, volume_dst_path: input.volumeDstPath ?? "/home/hacker" }), input.userUUID, input.nodeUUID),
      db.prepare(
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
      db.prepare(
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
      db.prepare(
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
      db.prepare("SELECT user_id FROM users WHERE user_uuid = ?").bind(input.userUUID),
      db.prepare(
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
      db.prepare(
        `SELECT
           v.volume_id,
           v.volume_uuid,
           v.snapshot_uuid,
           v.max_size_bytes,
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
      db.prepare(
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
    throw workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409, error);
  }
}

function parseClaimRows(results: D1Result<unknown>[]): ClaimRows {
  return {
    operationChanges: results[0].meta.changes,
    workspaceRows: rows<WorkspaceInsertRow>(results[3]),
    userRows: rows<UserRow>(results[4]),
    existingWorkspaceRows: rows<ExistingWorkspaceRow>(results[5]),
    homeVolumeRows: rows<HomeVolumeRow>(results[6]),
    targetNodeRows: rows<TargetNodeRow>(results[7]),
  };
}

function validClaimRows(claimRows: ClaimRows) {
  return (
    claimRows.operationChanges === 1 &&
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
    operationUuid: input.workspaceUuid,
    exportSnapshotUuid: input.exportSnapshotUuid!,
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
      maxSizeBytes: homeVolume.max_size_bytes,
      authoritativeNode,
    },
  };
}
