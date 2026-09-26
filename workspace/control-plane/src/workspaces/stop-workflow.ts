import { Effect } from "effect";
import { NodeClient } from "../node-client.ts";
import { commitWorkflow, rollbackOnFailure } from "./lifecycle.ts";
import { WorkspaceStore } from "./store.ts";

export const stopWorkspaceWorkflow = Effect.fn("stopWorkspaceWorkflow")(function*(userUUID: string) {
  const store = yield* WorkspaceStore;
  const nodes = yield* NodeClient;
  const claim = yield* commitWorkflow(
    rollbackOnFailure(store.claimStop(userUUID), store.failStop),
    (claim) => Effect.gen(function*() {
      // Finish recording a successful stop even if the HTTP caller disconnects.
      yield* nodes.stopWorkspace(claim.workspace.node, claim.workspace.workspaceUuid);
      yield* store.completeStop(claim);
    }),
  );
  return { workspace_uuid: claim.workspace.workspaceUuid, stopped: true };
});
