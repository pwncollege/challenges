import { Effect } from "effect";
import { NodeClient } from "../node-client.ts";
import type { Emit } from "./events.ts";
import { workspaceError } from "./errors.ts";
import { commitWorkflow, rollbackOnFailure } from "./lifecycle.ts";
import { WorkspaceStore } from "./store.ts";
import type { StartWorkspaceRequest } from "./schemas.ts";
import { ensureVolumeAvailableOnTarget } from "./volume-placement.ts";

export const startWorkspaceWorkflow = Effect.fn("startWorkspaceWorkflow")(function*(
  userUUID: string,
  payload: StartWorkspaceRequest,
  emit: Emit,
) {
  const store = yield* WorkspaceStore;
  const nodes = yield* NodeClient;
  const workspaceUuid = crypto.randomUUID();
  yield* emit({ event: "status", phase: "claiming", message: "Claiming workspace start" });

  const { claim } = yield* commitWorkflow(Effect.gen(function*() {
    const claim = yield* rollbackOnFailure(store.claimStart(userUUID, payload, workspaceUuid), store.failStart);
    const existing = claim.existingWorkspace;
    if (existing && existing.status !== "running") {
      return yield* workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409);
    }
    if (existing) {
      yield* emit({ event: "status", phase: "stopping_existing_workspace", message: "Stopping existing workspace" });
      yield* rollbackOnFailure(
        nodes.stopWorkspace(existing.node, existing.workspaceUuid),
        () => store.clearStoppedWorkspace(claim, existing.workspaceId),
      );
    }

    const homeVolume = yield* ensureVolumeAvailableOnTarget(claim, emit);
    yield* emit({ event: "status", phase: "starting", message: "Starting container" });
    yield* rollbackOnFailure(
      nodes.startWorkspace(claim.targetNode, workspaceUuid, {
        runtime_config: payload.runtime_config,
        volume: { volume_uuid: homeVolume.volumeUuid, dst_path: payload.volume_dst_path ?? "/home/hacker" },
      }),
      () => nodes.stopWorkspace(claim.targetNode, workspaceUuid),
    );
    return { claim, homeVolume };
  }), ({ claim, homeVolume }) => store.completeStart(claim, homeVolume));

  yield* emit({
    event: "complete", workspace_uuid: workspaceUuid, url: `${claim.targetNode.baseUrl}/w/${workspaceUuid}/`,
  });
});
