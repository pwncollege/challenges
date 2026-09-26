import { Effect, Layer } from "effect";
import { HttpRouter, HttpServerRequest, HttpServerResponse } from "effect/unstable/http";
import { SnapshotStore } from "../storage.ts";
import { workspaceError } from "../workspaces/errors.ts";

const transferRequest = Effect.fn("transferRequest")(function*(method: "GET" | "PUT") {
  const snapshots = yield* SnapshotStore;
  const request = yield* HttpServerRequest.toWeb(yield* HttpServerRequest.HttpServerRequest);
  yield* snapshots.verifyTransfer(request.url, method);
  const params = yield* HttpRouter.params;
  return { snapshots, request, volumeUUID: params.volumeUUID!, snapshotUUID: params.snapshotUUID! };
});

export const VolumeRoutes = Layer.mergeAll(
  HttpRouter.add("GET", "/api/volumes/:volumeUUID/snapshots/:snapshotUUID", Effect.gen(function*() {
    const { snapshots, volumeUUID, snapshotUUID } = yield* transferRequest("GET");
    return HttpServerResponse.fromWeb(new Response(yield* snapshots.read(volumeUUID, snapshotUUID)));
  })),
  HttpRouter.add("PUT", "/api/volumes/:volumeUUID/snapshots/:snapshotUUID", Effect.gen(function*() {
    const { snapshots, request, volumeUUID, snapshotUUID } = yield* transferRequest("PUT");
    const length = request.headers.get("content-length");
    if (!length || !/^\d+$/.test(length) || !Number.isSafeInteger(Number(length))) {
      return yield* workspaceError("length_required", "Snapshot uploads require Content-Length", 411);
    }
    const body = request.body;
    if (!body) return yield* workspaceError("invalid_request", "Missing snapshot body", 400);
    const key = yield* snapshots.upload(volumeUUID, snapshotUUID, body);
    return HttpServerResponse.jsonUnsafe({ key, uploaded: true });
  }), { uninterruptible: true }),
);
