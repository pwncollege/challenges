import { Effect } from "effect";
import { NodeClient } from "../node-client.ts";
import { SnapshotStore } from "../storage.ts";
import type { Emit } from "./events.ts";
import { workspaceError } from "./errors.ts";
import { WorkspaceStore } from "./store.ts";
import type { StartWorkspaceRequest } from "./schemas.ts";

export const startWorkspaceWorkflow = Effect.fn("startWorkspaceWorkflow")(function*(
  userUUID: string,
  payload: StartWorkspaceRequest,
  emit: Emit,
) {
  const store = yield* WorkspaceStore;
  const nodes = yield* NodeClient;
  const snapshots = yield* SnapshotStore;
  const workspaceUuid = crypto.randomUUID();
  yield* emit({ event: "status", phase: "claiming", message: "Claiming workspace start" });
  const claim = yield* store.claimStart(userUUID, payload, workspaceUuid);
  let home = claim.homeVolume;
  const existing = claim.existingWorkspace;
  const moving = home.authoritativeNode && home.authoritativeNode.nodeId !== claim.targetNode.nodeId;
  if (existing && (existing.status !== "running" ||
      (existing.node.nodeId !== claim.targetNode.nodeId && existing.node.nodeId !== home.authoritativeNode?.nodeId))) {
    yield* store.failStart(claim);
    return yield* workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409);
  }

  // Once a command could have changed a node, keep the durable claim on failure.
  // Its workspace UUID, source placement, and snapshot plan permit reconciliation.
  if (moving) {
    yield* emit({ event: "status", phase: "reclaiming_volume", message: "Moving home from its current node" });
    const snapshotUuid = claim.exportSnapshotUuid;
    const uploadUrl = yield* snapshots.transferUrl("PUT", home.volumeUuid, snapshotUuid);
    yield* nodes.exportVolume(home.authoritativeNode!, home.volumeUuid, snapshotUuid, uploadUrl, existing?.workspaceUuid);
    home = { ...home, snapshotUuid, authoritativeNode: null };
  }
  const snapshot = home.snapshotUuid ? {
    snapshot_uuid: home.snapshotUuid,
    download_url: yield* snapshots.transferUrl("GET", home.volumeUuid, home.snapshotUuid),
  } : null;
  yield* emit({ event: "status", phase: "starting", message: "Starting workspace" });
  yield* nodes.startWorkspace(claim.targetNode, workspaceUuid, {
    runtime_config: payload.runtime_config,
    ...(!moving && existing ? { replace_workspace_uuid: existing.workspaceUuid } : {}),
    volume: {
      volume_uuid: home.volumeUuid, dst_path: payload.volume_dst_path ?? "/home/hacker",
      max_size_bytes: home.maxSizeBytes, snapshot,
    },
  }).pipe(Effect.catch((error) => Effect.gen(function*() {
    if (!moving && error.operationStarted === false) yield* store.failStart(claim);
    return yield* error;
  })));
  yield* store.completeStart(claim, home);
  yield* emit({ event: "complete", workspace_uuid: workspaceUuid, url: `${claim.targetNode.baseUrl}/w/${workspaceUuid}/` });
}, Effect.uninterruptible);
