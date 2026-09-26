export type User = {
  userId: number;
  userUUID: string;
};

export type NodeStatus = "active" | "draining" | "disabled";

export type Node = {
  nodeId: number;
  nodeUUID: string;
  baseUrl: string;
  status: NodeStatus;
};

export type NodeRef = {
  nodeId: number;
  nodeUUID: string;
  baseUrl: string;
};

export type WorkspaceStatus = "creating" | "running" | "destroying";

export type RuntimeConfig = {
  container_image_ref: string;
  entrypoint?: string[];
  env?: Record<string, string>;
};

export type HomeVolume = {
  volumeId: number;
  volumeUuid: string;
  snapshotUuid: string | null;
  authoritativeNode: null | NodeRef;
};

export type ClaimedWorkspaceStart = {
  userId: number;
  workspace: {
    workspaceId: number;
    workspaceUuid: string;
  };
  targetNode: NodeRef;
  existingWorkspace: null | {
    workspaceId: number;
    workspaceUuid: string;
    status: WorkspaceStatus;
    node: NodeRef;
  };
  homeVolume: HomeVolume;
};

export type ClaimWorkspaceStartInput = {
  userUUID: string;
  nodeUUID: string;
  newVolumeUUID: string;
  workspaceUuid: string;
  runtimeConfig: RuntimeConfig;
  now: number;
};

export type CurrentWorkspace = {
  workspaceId: number;
  workspaceUuid: string;
  status: WorkspaceStatus;
  node: NodeRef;
};
