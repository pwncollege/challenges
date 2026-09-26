import type { Bindings } from "../common.ts";
import { unixSeconds } from "../common.ts";
import { NodeClient } from "../node-client.ts";
import { WorkspaceError, workspaceError } from "./errors.ts";
import { claimWorkspaceStop, completeWorkspaceStop, failWorkspaceStop } from "./stop-claim.ts";

export async function stopWorkspaceWorkflow(env: Bindings, userUUID: string) {
  const claim = await claimWorkspaceStop(env, userUUID, unixSeconds());
  try {
    const response = await new NodeClient(env, claim.workspace.node).stopWorkspace(claim.workspace.workspaceUuid);
    if (!response.ok && response.status !== 404) throw workspaceError("workspace_stop_failed");
    await completeWorkspaceStop(env, claim.userId, claim.workspace.workspaceId);
    return { workspace_uuid: claim.workspace.workspaceUuid, stopped: true };
  } catch (error) {
    await failWorkspaceStop(env, claim.userId, claim.workspace.workspaceId, unixSeconds());
    if (error instanceof WorkspaceError) throw error;
    throw workspaceError("internal_error", "Workspace stop failed", 500);
  }
}
