import type { Bindings } from "../common.ts";
import { rows } from "../common.ts";
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

function expectChanges(result: D1Result<unknown>, expected: number, code = "database_conflict") {
  if (result.meta.changes !== expected) {
    throw workspaceError(code, code);
  }
}

export async function claimWorkspaceStop(env: Bindings, userUUID: string, now: number) {
  let results: D1Result<unknown>[];
  try {
    results = await env.DB.batch([
      env.DB.prepare(
        `INSERT INTO user_workspace_locks (user_id, locked_at)
         SELECT user_id, ?
         FROM users
         WHERE user_uuid = ?`,
      ).bind(now, userUUID),
      env.DB.prepare("SELECT user_id FROM users WHERE user_uuid = ?").bind(userUUID),
      env.DB.prepare(
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
      env.DB.prepare(
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
    await releaseWorkspaceStopClaim(env, claimRows.userRows[0].user_id);
    throw workspaceError("workspace_not_found", "Workspace not found", 404);
  }
  if (claimRows.workspaceRows[0].status !== "running" || claimRows.destroyingChanges !== 1) {
    await releaseWorkspaceStopClaim(env, claimRows.userRows[0].user_id);
    throw workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409);
  }

  const workspace = claimRows.workspaceRows[0];
  return {
    userId: claimRows.userRows[0].user_id,
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

export async function completeWorkspaceStop(env: Bindings, userId: number, workspaceId: number) {
  const results = await env.DB.batch([
    env.DB.prepare("DELETE FROM user_workspaces WHERE user_id = ? AND workspace_id = ?").bind(userId, workspaceId),
    env.DB.prepare("DELETE FROM workspaces WHERE workspace_id = ?").bind(workspaceId),
    env.DB.prepare("DELETE FROM user_workspace_locks WHERE user_id = ?").bind(userId),
  ]);
  expectChanges(results[0], 1);
  expectChanges(results[1], 1);
  expectChanges(results[2], 1);
}

export async function failWorkspaceStop(env: Bindings, userId: number, workspaceId: number, now: number) {
  await env.DB.batch([
    env.DB.prepare("UPDATE workspaces SET status = 'running', updated_at = ? WHERE workspace_id = ?").bind(
      now,
      workspaceId,
    ),
    env.DB.prepare("DELETE FROM user_workspace_locks WHERE user_id = ?").bind(userId),
  ]).catch(() => undefined);
}

async function releaseWorkspaceStopClaim(env: Bindings, userId: number) {
  await env.DB.prepare("DELETE FROM user_workspace_locks WHERE user_id = ?").bind(userId).run().catch(() => undefined);
}

function parseStopClaimRows(results: D1Result<unknown>[]): StopClaimRows {
  return {
    lockChanges: results[0].meta.changes,
    userRows: rows<{ user_id: number }>(results[1]),
    workspaceRows: rows<StopClaimRows["workspaceRows"][number]>(results[2]),
    destroyingChanges: results[3].meta.changes,
  };
}
