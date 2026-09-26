import { rows } from "../common.ts";
import { expectChanges, owned, ownsOperation, releaseOperation, type OperationClaim } from "./operations.ts";
import { workspaceError } from "./errors.ts";
import type { CurrentWorkspace, WorkspaceStatus } from "./types.ts";

type StopClaimRows = {
  lockChanges: number;
  destroyingChanges: number;
  userRows: { user_id: number }[];
  workspaceRows: {
    workspace_id: number;
    workspace_uuid: string;
    status: WorkspaceStatus;
    node_id: number;
    node_uuid: string;
    base_url: string;
  }[];
};

export async function claimWorkspaceStop(db: D1Database, userUUID: string, operationUuid: string, now: number) {
  let results: D1Result<unknown>[];
  try {
    results = await db.batch([
      db.prepare(
        `INSERT INTO workspace_operations (user_id, operation_uuid, kind, created_at)
         SELECT user_id, ?, 'stop', ?
         FROM users
         WHERE user_uuid = ?`,
      ).bind(operationUuid, now, userUUID),
      db.prepare("SELECT user_id FROM users WHERE user_uuid = ?").bind(userUUID),
      db.prepare(
        `SELECT
           ws.workspace_id,
           ws.workspace_uuid,
           ws.status,
           ws.node_id,
           n.node_uuid,
           n.base_url
         FROM users u
         JOIN user_workspaces uw
           ON uw.user_id = u.user_id
         JOIN workspaces ws
           ON ws.workspace_id = uw.workspace_id
         JOIN nodes n
           ON n.node_id = ws.node_id
         WHERE u.user_uuid = ?`,
      ).bind(userUUID),
      db.prepare(
        `UPDATE workspaces
         SET status = 'destroying', updated_at = ?
         WHERE workspace_id = (
           SELECT uw.workspace_id
           FROM users u
           JOIN user_workspaces uw
             ON uw.user_id = u.user_id
           WHERE u.user_uuid = ?
         )
           AND status = 'running'`,
      ).bind(now, userUUID),
    ]);
  } catch (error) {
    throw workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409, error);
  }

  const claimRows = parseStopClaimRows(results);
  if (claimRows.userRows.length === 0) throw workspaceError("user_not_found", "User not found", 404);
  if (claimRows.lockChanges !== 1) throw workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409);
  if (claimRows.workspaceRows.length === 0) {
    await releaseOperation(db, { userId: claimRows.userRows[0].user_id, operationUuid }).run();
    throw workspaceError("workspace_not_found", "Workspace not found", 404);
  }
  if (claimRows.workspaceRows[0].status !== "running" || claimRows.destroyingChanges !== 1) {
    await releaseOperation(db, { userId: claimRows.userRows[0].user_id, operationUuid }).run();
    throw workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409);
  }

  const workspace = claimRows.workspaceRows[0];
  return {
    userId: claimRows.userRows[0].user_id,
    operationUuid,
    workspace: {
      workspaceId: workspace.workspace_id,
      workspaceUuid: workspace.workspace_uuid,
      status: workspace.status,
      node: {
        nodeId: workspace.node_id,
        nodeUUID: workspace.node_uuid,
        baseUrl: workspace.base_url,
      },
    } satisfies CurrentWorkspace,
  };
}

export async function completeWorkspaceStop(db: D1Database, claim: OperationClaim, workspaceId: number) {
  const results = await db.batch([
    owned(db, claim, `DELETE FROM user_workspaces WHERE workspace_id = ? AND ${ownsOperation}`, workspaceId),
    owned(db, claim, `DELETE FROM workspaces WHERE workspace_id = ? AND ${ownsOperation}`, workspaceId),
    releaseOperation(db, claim),
  ]);
  for (const result of results) expectChanges(result);
}

function parseStopClaimRows(results: D1Result<unknown>[]): StopClaimRows {
  return {
    lockChanges: results[0].meta.changes,
    userRows: rows<{ user_id: number }>(results[1]),
    workspaceRows: rows<StopClaimRows["workspaceRows"][number]>(results[2]),
    destroyingChanges: results[3].meta.changes,
  };
}
