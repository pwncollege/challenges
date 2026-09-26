import type { Bindings } from "./common.ts";
import { unixSeconds } from "./common.ts";
import { canonicalRequest, importPrivateKey, sha256Hex, signCanonical } from "./signing.ts";

export type NodeTarget = {
  nodeId: number;
  baseUrl: string;
};

export class NodeClient {
  private readonly privateKey: Promise<CryptoKey>;
  private readonly baseUrl: string;

  constructor(env: Bindings, node: NodeTarget) {
    this.privateKey = importPrivateKey(env.PWN_WORKSPACE_PRIVATE_KEY_B64);
    this.baseUrl = node.baseUrl;
  }

  private async fetchSigned(method: string, path: string, body?: unknown) {
    const url = new URL(path, this.baseUrl);
    const bodyText = body === undefined ? "" : JSON.stringify(body);
    const timestamp = String(unixSeconds());
    const bodyHash = await sha256Hex(bodyText);
    const canonical = canonicalRequest(method, `${url.pathname}${url.search}`, timestamp, bodyHash);
    const signature = await signCanonical(await this.privateKey, canonical);
    return fetch(url, {
      method,
      headers: {
        "content-type": "application/json",
        "x-pwn-workspace-timestamp": timestamp,
        "x-pwn-workspace-signature": signature,
      },
      body: method === "GET" || method === "HEAD" ? undefined : bodyText,
    });
  }

  health() {
    return this.fetchSigned("GET", "/api/health");
  }

  stopWorkspace(workspaceUuid: string) {
    return this.fetchSigned("POST", `/api/workspaces/${workspaceUuid}/stop`);
  }

  startWorkspace(workspaceUuid: string, body: unknown) {
    return this.fetchSigned("POST", `/api/workspaces/${workspaceUuid}/start`, body);
  }

  snapshotVolume(volumeUuid: string, snapshotUuid: string) {
    return this.fetchSigned("POST", `/api/volumes/${volumeUuid}/snapshot`, {
      snapshot_uuid: snapshotUuid,
    });
  }

  uploadVolume(volumeUuid: string, snapshotUuid: string, url: string) {
    return this.fetchSigned("POST", `/api/volumes/${volumeUuid}/upload`, {
      snapshot_uuid: snapshotUuid,
      url,
    });
  }

  downloadVolume(volumeUuid: string, snapshotUuid: string, url: string) {
    return this.fetchSigned("POST", `/api/volumes/${volumeUuid}/download`, {
      snapshot_uuid: snapshotUuid,
      url,
    });
  }

  deactivateVolume(volumeUuid: string) {
    return this.fetchSigned("POST", `/api/volumes/${volumeUuid}/deactivate`);
  }

  activateVolume(volumeUuid: string, snapshotUuid: string | null) {
    return this.fetchSigned("POST", `/api/volumes/${volumeUuid}/activate`, {
      snapshot_uuid: snapshotUuid,
    });
  }
}
