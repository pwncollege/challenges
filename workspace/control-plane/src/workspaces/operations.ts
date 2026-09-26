import { workspaceError } from "./errors.ts";

export type OperationClaim = { userId: number; operationUuid: string };

export const ownsOperation = "EXISTS (SELECT 1 FROM workspace_operations WHERE user_id = ? AND operation_uuid = ?)";

export function owned(db: D1Database, claim: OperationClaim, sql: string, ...values: (string | number | null)[]) {
  return db.prepare(sql).bind(...values, claim.userId, claim.operationUuid);
}

export function releaseOperation(db: D1Database, claim: OperationClaim) {
  return db.prepare("DELETE FROM workspace_operations WHERE user_id = ? AND operation_uuid = ?")
    .bind(claim.userId, claim.operationUuid);
}

export function expectChanges(result: D1Result<unknown>, expected = 1) {
  if (result.meta.changes !== expected) throw workspaceError("workspace_operation_conflict", "Workspace operation no longer owns its claim", 409);
}
