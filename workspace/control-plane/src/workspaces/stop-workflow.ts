import { Effect } from "effect";
import { NodeClient } from "../node-client.ts";
import { WorkspaceStore } from "./store.ts";

export const stopWorkspaceWorkflow = Effect.fn("stopWorkspaceWorkflow")(function*(userUUID: string) {
  const store = yield* WorkspaceStore;
  const nodes = yield* NodeClient;
  const claim = yield* store.claimStop(userUUID);
  // An uncertain stop keeps its claim; a later start must not race a live node.
  yield* nodes.stopWorkspace(claim.workspace.node, claim.workspace.workspaceUuid);
  yield* store.completeStop(claim);
  return { workspace_uuid: claim.workspace.workspaceUuid, stopped: true };
}, Effect.uninterruptible);
