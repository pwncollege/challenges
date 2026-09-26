import { Effect } from "effect";
import { NodeClient } from "../node-client.ts";
import { SnapshotStore } from "../storage.ts";
import { WorkspaceStore } from "./store.ts";
import type { Emit } from "./events.ts";
import { rollbackOnFailure } from "./lifecycle.ts";
import type { ClaimedWorkspaceStart } from "./types.ts";

export const ensureVolumeAvailableOnTarget = Effect.fn("ensureVolumeAvailableOnTarget")(function*(
  claim: ClaimedWorkspaceStart,
  emit: Emit,
) {
  let volume = claim.homeVolume;
  const targetNode = claim.targetNode;
  const nodes = yield* NodeClient;
  const store = yield* WorkspaceStore;
  const snapshots = yield* SnapshotStore;
  if (volume.authoritativeNode && volume.authoritativeNode.nodeId !== targetNode.nodeId) {
    yield* emit({ event: "status", phase: "reclaiming_volume", message: "Reclaiming user volume" });
    const source = volume.authoritativeNode;
    const original = volume;
    const snapshotUuid = crypto.randomUUID();
    const uploadUuid = crypto.randomUUID();
    volume = yield* rollbackOnFailure(Effect.gen(function*() {
      yield* nodes.snapshotVolume(source, original.volumeUuid, snapshotUuid);
      const url = yield* snapshots.transferUrl("PUT", original.volumeUuid, snapshotUuid, uploadUuid);
      yield* nodes.uploadVolume(source, original.volumeUuid, snapshotUuid, url);
      yield* snapshots.commit(original.volumeUuid, snapshotUuid, uploadUuid);
      return { ...original, snapshotUuid, authoritativeNode: null };
    }), () => store.preserveSnapshot(claim, original.volumeId, snapshotUuid));

    // The old workspace is stopped and its snapshot is saved; deletion is cleanup.
    yield* nodes.deactivateVolume(source, volume.volumeUuid).pipe(
      Effect.catch((error) => Effect.logWarning("Failed to deactivate previous home volume", {
        volume_uuid: original.volumeUuid, node_uuid: source.nodeUUID, error,
      })),
    );
  }

  if (volume.authoritativeNode?.nodeId !== targetNode.nodeId) {
    yield* emit({ event: "status", phase: "activating_volume", message: "Activating user volume" });
    if (volume.snapshotUuid) {
      const url = yield* snapshots.transferUrl("GET", volume.volumeUuid, volume.snapshotUuid);
      yield* nodes.downloadVolume(targetNode, volume.volumeUuid, volume.snapshotUuid, url);
    }
    yield* nodes.deactivateVolume(targetNode, volume.volumeUuid);
    yield* rollbackOnFailure(
      nodes.activateVolume(targetNode, volume.volumeUuid, volume.snapshotUuid, claim.operationUuid),
      () => nodes.deactivateVolume(targetNode, volume.volumeUuid),
    );
    volume = { ...volume, authoritativeNode: targetNode };
  }
  return volume;
});
