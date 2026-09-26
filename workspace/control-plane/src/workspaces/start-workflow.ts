import type { Bindings } from "../common.ts";
import { unixSeconds } from "../common.ts";
import { NodeClient } from "../node-client.ts";
import type { Emit } from "./events.ts";
import { contentfulStatus, workspaceError } from "./errors.ts";
import { claimWorkspaceStart, completeWorkspaceStart, failWorkspaceStart } from "./start-claim.ts";
import type { StartWorkspaceRequest } from "./schemas.ts";
import type { ClaimedWorkspaceStart, HomeVolume } from "./types.ts";
import { ensureVolumeAvailableOnTarget } from "./volume-placement.ts";

type Compensation = {
  run: () => Promise<void>;
};

type NodeErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

class CompensationStack {
  private readonly items: Compensation[] = [];

  add(run: () => Promise<void>) {
    this.items.push({ run });
  }

  async runAll() {
    for (let index = this.items.length - 1; index >= 0; index -= 1) {
      await this.items[index].run().catch(() => undefined);
    }
  }
}

export async function startWorkspaceWorkflow(
  env: Bindings,
  userUUID: string,
  payload: StartWorkspaceRequest,
  emit: Emit,
) {
  const workspaceUuid = crypto.randomUUID();
  const compensations = new CompensationStack();
  const claim = await claimStart(env, userUUID, payload, workspaceUuid, emit);
  const nodeClient = new NodeClient(env, claim.targetNode);
  let homeVolume = claim.homeVolume;

  try {
    await stopExistingWorkspace(env, claim, emit, compensations);
    homeVolume = await ensureVolumeAvailableOnTarget(env, {
      volume: claim.homeVolume,
      targetNode: claim.targetNode,
      targetClient: nodeClient,
      compensations,
      emit,
    });
    await startContainerOnNode({
      workspaceUuid,
      payload,
      homeVolume,
      nodeClient,
      compensations,
      emit,
    });
    await completeWorkspaceStart(env, {
      userId: claim.userId,
      workspaceId: claim.workspace.workspaceId,
      oldWorkspaceId: claim.existingWorkspace?.workspaceId ?? null,
      volumeId: homeVolume.volumeId,
      targetNodeId: claim.targetNode.nodeId,
      snapshotUuid: homeVolume.snapshotUuid,
      now: unixSeconds(),
    });
  } catch (error) {
    await compensations.runAll();
    await failWorkspaceStart(env, claim.userId, claim.workspace.workspaceId, claim.homeVolume.volumeId);
    throw error;
  }

  await emit({
    event: "complete",
    workspace_uuid: workspaceUuid,
    url: `${claim.targetNode.baseUrl}/w/${workspaceUuid}/`,
  });
}

async function claimStart(
  env: Bindings,
  userUUID: string,
  payload: StartWorkspaceRequest,
  workspaceUuid: string,
  emit: Emit,
) {
  await emit({ event: "status", phase: "claiming", message: "Claiming workspace start" });
  const claim = await claimWorkspaceStart(env, {
    userUUID,
    nodeUUID: payload.node_uuid,
    newVolumeUUID: crypto.randomUUID(),
    workspaceUuid,
    runtimeConfig: payload.runtime_config,
    now: unixSeconds(),
  });

  if (claim.existingWorkspace && claim.existingWorkspace.status !== "running") {
    await failWorkspaceStart(env, claim.userId, claim.workspace.workspaceId, claim.homeVolume.volumeId);
    throw workspaceError("workspace_operation_in_progress", "Workspace operation in progress", 409);
  }
  return claim;
}

async function stopExistingWorkspace(
  env: Bindings,
  claim: ClaimedWorkspaceStart,
  emit: Emit,
  compensations: CompensationStack,
) {
  const existingWorkspace = claim.existingWorkspace;
  if (!existingWorkspace) return;
  await emit({ event: "status", phase: "stopping_existing_workspace", message: "Stopping existing workspace" });
  const response = await new NodeClient(env, existingWorkspace.node).stopWorkspace(existingWorkspace.workspaceUuid);
  if (!response.ok && response.status !== 404) throw workspaceError("workspace_stop_failed");
  compensations.add(() => clearStoppedCurrentWorkspace(env, claim.userId, existingWorkspace.workspaceId));
}

async function clearStoppedCurrentWorkspace(env: Bindings, userId: number, workspaceId: number) {
  await env.DB.batch([
    env.DB.prepare("DELETE FROM user_workspaces WHERE user_id = ? AND workspace_id = ?").bind(userId, workspaceId),
    env.DB.prepare("DELETE FROM workspaces WHERE workspace_id = ?").bind(workspaceId),
  ]).catch(() => undefined);
}

async function startContainerOnNode(input: {
  workspaceUuid: string;
  payload: StartWorkspaceRequest;
  homeVolume: HomeVolume;
  nodeClient: NodeClient;
  compensations: CompensationStack;
  emit: Emit;
}) {
  await input.emit({ event: "status", phase: "starting", message: "Starting container" });
  const startResponse = await input.nodeClient.startWorkspace(input.workspaceUuid, {
    runtime_config: input.payload.runtime_config,
    volume: {
      volume_uuid: input.homeVolume.volumeUuid,
      dst_path: input.payload.volume_dst_path ?? "/home/hacker",
    },
  });
  if (!startResponse.ok) {
    const error = await startResponse.json<NodeErrorBody>().catch((): NodeErrorBody => ({}));
    throw workspaceError(
      error.error?.code ?? "workspace_start_failed",
      error.error?.message,
      contentfulStatus(startResponse.status),
    );
  }
  input.compensations.add(async () => {
    await input.nodeClient.stopWorkspace(input.workspaceUuid);
  });
}
