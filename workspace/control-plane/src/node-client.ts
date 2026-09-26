import { Context, Effect, Layer, Schema } from "effect";
import { FetchHttpClient } from "effect/unstable/http";
import { Environment, unixSeconds } from "./common.ts";
import { canonicalRequest, importPrivateKey, sha256Hex, signCanonical } from "./signing.ts";
import { contentfulStatus, fromPromise, workspaceError } from "./workspaces/errors.ts";
import { NodeErrorResponse, type NodeStartRequest } from "./workspaces/schemas.ts";
import type { NodeRef } from "./workspaces/types.ts";

const decodeNodeError = Schema.decodeUnknownEffect(NodeErrorResponse);

export class NodeClient extends Context.Service<NodeClient>()("control-plane/NodeClient", {
  make: Effect.gen(function*() {
    const env = yield* Environment;
    const fetch = yield* FetchHttpClient.Fetch;
    const privateKey = yield* Effect.cached(fromPromise(() => importPrivateKey(env.PWN_WORKSPACE_PRIVATE_KEY_B64)));

    const command = Effect.fn("NodeClient.command")(function*(
      node: NodeRef,
      path: string,
      code: string,
      body?: unknown,
      options: { forwardError?: boolean } = {},
    ) {
      const url = new URL(path, node.baseUrl);
      const bodyText = body === undefined ? "" : JSON.stringify(body);
      const timestamp = String(unixSeconds());
      const key = yield* privateKey;
      const signature = yield* fromPromise(async () => {
        const bodyHash = await sha256Hex(bodyText);
        return signCanonical(key, canonicalRequest("POST", `${url.pathname}${url.search}`, timestamp, bodyHash));
      });
      const response = yield* Effect.tryPromise({
        try: (signal) => fetch(url, {
          method: "POST", signal, body: bodyText,
          headers: {
            "content-type": "application/json",
            "x-pwn-workspace-timestamp": timestamp,
            "x-pwn-workspace-signature": signature,
          },
        }),
        catch: (cause) => workspaceError("node_unavailable", "Workspace node unavailable", 502, cause),
      });
      if (response.ok) return;
      if (options.forwardError) {
        const error = yield* fromPromise(() => response.json()).pipe(
          Effect.flatMap(decodeNodeError),
          Effect.map((body) => body.error),
          Effect.catch(() => Effect.succeed({ code, message: code })),
        );
        return yield* workspaceError(error.code, error.message, contentfulStatus(response.status));
      }
      return yield* workspaceError(code);
    });

    return {
      stopWorkspace: (node: NodeRef, workspaceUuid: string) =>
        command(node, `/api/workspaces/${workspaceUuid}/stop`, "workspace_stop_failed"),
      startWorkspace: (node: NodeRef, workspaceUuid: string, body: NodeStartRequest) =>
        command(node, `/api/workspaces/${workspaceUuid}/start`, "workspace_start_failed", body, { forwardError: true }),
      snapshotVolume: (node: NodeRef, volumeUuid: string, snapshotUuid: string) =>
        command(node, `/api/volumes/${volumeUuid}/snapshot`, "volume_reclaim_failed", { snapshot_uuid: snapshotUuid }),
      uploadVolume: (node: NodeRef, volumeUuid: string, snapshotUuid: string, url: string) =>
        command(node, `/api/volumes/${volumeUuid}/upload`, "volume_reclaim_failed", { snapshot_uuid: snapshotUuid, url }),
      downloadVolume: (node: NodeRef, volumeUuid: string, snapshotUuid: string, url: string) =>
        command(node, `/api/volumes/${volumeUuid}/download`, "volume_activation_failed", { snapshot_uuid: snapshotUuid, url }),
      deactivateVolume: (node: NodeRef, volumeUuid: string) =>
        command(node, `/api/volumes/${volumeUuid}/deactivate`, "volume_activation_failed"),
      activateVolume: (node: NodeRef, volumeUuid: string, snapshotUuid: string | null, activationUuid: string) =>
        command(node, `/api/volumes/${volumeUuid}/activate`, "volume_activation_failed", { snapshot_uuid: snapshotUuid, activation_uuid: activationUuid }),
    };
  }),
}) {
  static readonly layer = Layer.effect(NodeClient, NodeClient.make);
}
