import type { Bindings } from "../common.ts";
import { unixSeconds } from "../common.ts";
import { NodeClient } from "../node-client.ts";
import { commitStagedSnapshot } from "../storage.ts";
import { transferUrl } from "../volumes/transfers.ts";
import type { Emit } from "./events.ts";
import { workspaceError } from "./errors.ts";
import type { HomeVolume, NodeRef } from "./types.ts";

type Compensations = {
  add(run: () => Promise<void>): void;
};

export async function ensureVolumeAvailableOnTarget(
  env: Bindings,
  input: {
    volume: HomeVolume;
    targetNode: NodeRef;
    targetClient: NodeClient;
    compensations: Compensations;
    emit: Emit;
  },
) {
  let volume = input.volume;
  if (volume.authoritativeNode && volume.authoritativeNode.nodeId !== input.targetNode.nodeId) {
    volume = await reclaimVolume(env, { ...input, volume });
  }

  if (volume.authoritativeNode?.nodeId !== input.targetNode.nodeId) {
    volume = await activateVolumeOnTarget(env, { ...input, volume });
  }
  return volume;
}

async function reclaimVolume(
  env: Bindings,
  input: {
    volume: HomeVolume;
    compensations: Compensations;
    emit: Emit;
  },
) {
  const { volume } = input;
  if (!volume.authoritativeNode) return volume;
  await input.emit({ event: "status", phase: "reclaiming_volume", message: "Reclaiming user volume" });
  const reclaimedSnapshotUuid = crypto.randomUUID();
  const uploadUuid = crypto.randomUUID();
  const oldNodeClient = new NodeClient(env, volume.authoritativeNode);

  let response = await oldNodeClient.snapshotVolume(volume.volumeUuid, reclaimedSnapshotUuid);
  if (!response.ok) throw workspaceError("volume_reclaim_failed");

  response = await oldNodeClient.uploadVolume(
    volume.volumeUuid,
    reclaimedSnapshotUuid,
    await transferUrl(env, "PUT", volume.volumeUuid, reclaimedSnapshotUuid, uploadUuid),
  );
  if (!response.ok) throw workspaceError("volume_reclaim_failed");

  if (!(await commitStagedSnapshot(env, volume.volumeUuid, reclaimedSnapshotUuid, uploadUuid))) {
    throw workspaceError("volume_reclaim_failed");
  }

  // The old workspace is stopped and its snapshot is saved; deletion is cleanup.
  try {
    response = await oldNodeClient.deactivateVolume(volume.volumeUuid);
    if (!response.ok) {
      console.warn("Failed to deactivate previous home volume", {
        volume_uuid: volume.volumeUuid,
        node_uuid: volume.authoritativeNode.nodeUUID,
        status: response.status,
      });
    }
  } catch (error) {
    console.warn("Failed to deactivate previous home volume", {
      volume_uuid: volume.volumeUuid,
      node_uuid: volume.authoritativeNode.nodeUUID,
      error: error instanceof Error ? error.message : String(error),
    });
  }
  input.compensations.add(() => preserveReclaimedSnapshot(env, volume.volumeId, reclaimedSnapshotUuid, unixSeconds()));
  return {
    ...volume,
    snapshotUuid: reclaimedSnapshotUuid,
    authoritativeNode: null,
  };
}

async function preserveReclaimedSnapshot(env: Bindings, volumeId: number, snapshotUuid: string, now: number) {
  await env.DB.prepare("UPDATE volumes SET node_id = NULL, snapshot_uuid = ?, updated_at = ? WHERE volume_id = ?")
    .bind(snapshotUuid, now, volumeId)
    .run()
    .catch(() => undefined);
}

async function activateVolumeOnTarget(
  env: Bindings,
  input: {
    volume: HomeVolume;
    targetNode: NodeRef;
    targetClient: NodeClient;
    compensations: Compensations;
    emit: Emit;
  },
) {
  const { targetClient, targetNode, volume } = input;
  await input.emit({ event: "status", phase: "activating_volume", message: "Activating user volume" });
  if (volume.snapshotUuid) {
    const response = await targetClient.downloadVolume(
      volume.volumeUuid,
      volume.snapshotUuid,
      await transferUrl(env, "GET", volume.volumeUuid, volume.snapshotUuid),
    );
    if (!response.ok) throw workspaceError("volume_activation_failed");
  }

  let response = await targetClient.deactivateVolume(volume.volumeUuid);
  if (!response.ok) throw workspaceError("volume_activation_failed");

  response = await targetClient.activateVolume(volume.volumeUuid, volume.snapshotUuid);
  if (!response.ok) throw workspaceError("volume_activation_failed");

  input.compensations.add(async () => {
    await new NodeClient(env, targetNode).deactivateVolume(volume.volumeUuid);
  });
  return {
    ...volume,
    authoritativeNode: targetNode,
  };
}
