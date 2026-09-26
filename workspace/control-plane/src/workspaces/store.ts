import { Context, Effect, Layer } from "effect";
import { Environment, rows, unixSeconds } from "../common.ts";
import { fromPromise } from "./errors.ts";
import { claimWorkspaceStart, completeWorkspaceStart, failWorkspaceStart } from "./start-claim.ts";
import { claimWorkspaceStop, completeWorkspaceStop } from "./stop-claim.ts";
import type { StartWorkspaceRequest } from "./schemas.ts";
import type { ClaimedWorkspaceStart, HomeVolume } from "./types.ts";

type StopClaim = Awaited<ReturnType<typeof claimWorkspaceStop>>;
type NodeRow = { node_uuid: string; base_url: string };

export class WorkspaceStore extends Context.Service<WorkspaceStore>()("control-plane/WorkspaceStore", {
  make: Effect.gen(function*() {
    const { DB: db } = yield* Environment;
    return {
      claimStart: (userUUID: string, payload: StartWorkspaceRequest, workspaceUuid: string) =>
        fromPromise(() => claimWorkspaceStart(db, {
          userUUID, nodeUUID: payload.node_uuid, workspaceUuid, runtimeConfig: payload.runtime_config,
          volumeDstPath: payload.volume_dst_path, newVolumeUUID: crypto.randomUUID(), now: unixSeconds(),
        })),
      completeStart: (claim: ClaimedWorkspaceStart, volume: HomeVolume) =>
        fromPromise(() => completeWorkspaceStart(db, {
          userId: claim.userId, operationUuid: claim.operationUuid, workspaceId: claim.workspace.workspaceId,
          oldWorkspaceId: claim.existingWorkspace?.workspaceId ?? null,
          volumeId: volume.volumeId, targetNodeId: claim.targetNode.nodeId,
          snapshotUuid: volume.snapshotUuid, now: unixSeconds(),
        })),
      failStart: (claim: ClaimedWorkspaceStart) =>
        fromPromise(() => failWorkspaceStart(db, claim, claim.workspace.workspaceUuid)),
      claimStop: (userUUID: string) => fromPromise(() => claimWorkspaceStop(db, userUUID, crypto.randomUUID(), unixSeconds())),
      completeStop: (claim: StopClaim) => fromPromise(() => completeWorkspaceStop(db, claim, claim.workspace.workspaceId)),
      findUser: (userUUID: string) => fromPromise(() => db.prepare(
        "SELECT user_uuid FROM users WHERE user_uuid = ?",
      ).bind(userUUID).first<{ user_uuid: string }>()),
      listNodes: (userUUID: string | null) => fromPromise(async () => {
        const activeNodes = db.prepare("SELECT node_uuid, base_url FROM nodes WHERE status = 'active' ORDER BY node_id");
        if (!userUUID) return { nodes: (await activeNodes.all<NodeRow>()).results ?? [] };
        const results = await db.batch([
          activeNodes,
          db.prepare(
            `SELECT n.node_uuid, n.base_url
             FROM users u
             JOIN user_home_volumes uhv ON uhv.user_id = u.user_id
             JOIN volumes v ON v.volume_id = uhv.volume_id
             LEFT JOIN nodes n ON n.node_id = v.node_id
             WHERE u.user_uuid = ?`,
          ).bind(userUUID),
        ]);
        const home = rows<{ node_uuid: string | null; base_url: string | null }>(results[1])[0];
        return {
          nodes: rows<NodeRow>(results[0]),
          current_home_node: home?.node_uuid && home.base_url ? { node_uuid: home.node_uuid, base_url: home.base_url } : null,
        };
      }),
    };
  }),
}) {
  static readonly layer = Layer.effect(WorkspaceStore, WorkspaceStore.make);
}
