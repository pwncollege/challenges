import { Context, Effect, Layer } from "effect";
import { Environment } from "./common.ts";
import { fromPromise, workspaceError } from "./workspaces/errors.ts";
import { transferUrl, verifyTransferURL } from "./volumes/transfers.ts";

function snapshotKey(volumeUUID: string, snapshotUUID: string) {
  return `snapshots/${volumeUUID}/${snapshotUUID}`;
}

export class SnapshotStore extends Context.Service<SnapshotStore>()("control-plane/SnapshotStore", {
  make: Effect.gen(function*() {
    const env = yield* Environment;
    const bucket = env.VOLUMES;
    return {
      read: (volumeUUID: string, snapshotUUID: string) =>
        fromPromise(() => bucket.get(snapshotKey(volumeUUID, snapshotUUID))).pipe(
          Effect.flatMap((object) => object
            ? Effect.succeed(object.body)
            : Effect.fail(workspaceError("snapshot_not_found", "Snapshot not found", 404))),
        ),
      upload: (volumeUUID: string, snapshotUUID: string, body: ReadableStream<Uint8Array>) => {
        const key = snapshotKey(volumeUUID, snapshotUUID);
        return fromPromise(() => bucket.put(key, body)).pipe(Effect.as(key));
      },
      transferUrl: (method: "GET" | "PUT", volumeUUID: string, snapshotUUID: string) =>
        fromPromise(() => transferUrl(env, method, volumeUUID, snapshotUUID)),
      verifyTransfer: (requestURL: string, method: "GET" | "PUT") =>
        fromPromise(() => verifyTransferURL(env, requestURL, method)).pipe(
          Effect.flatMap((valid) => valid
            ? Effect.void
            : Effect.fail(workspaceError("invalid_signature", "Invalid transfer signature", 401))),
        ),
    };
  }),
}) {
  static readonly layer = Layer.effect(SnapshotStore, SnapshotStore.make);
}
