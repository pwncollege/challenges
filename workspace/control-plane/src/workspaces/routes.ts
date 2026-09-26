import { Effect, Layer } from "effect";
import { HttpRouter, HttpServerRequest, HttpServerResponse } from "effect/unstable/http";
import { Environment } from "../common.ts";
import { ndjsonStream } from "./events.ts";
import { fromPromise, workspaceError } from "./errors.ts";
import { sessionUserUUID } from "../session.ts";
import { normalizeVolumePath, startSchema } from "./schemas.ts";
import { startWorkspaceWorkflow } from "./start-workflow.ts";
import { stopWorkspaceWorkflow } from "./stop-workflow.ts";

const requireUser = Effect.gen(function*() {
  const env = yield* Environment;
  const request = yield* HttpServerRequest.HttpServerRequest;
  const userUUID = yield* fromPromise(() => sessionUserUUID(env, request.headers.cookie));
  if (!userUUID) return yield* workspaceError("unauthorized", "Login required", 401);
  return userUUID;
});

export const WorkspaceRoutes = Layer.mergeAll(
  HttpRouter.add("POST", "/api/workspaces/start", Effect.gen(function*() {
    const userUUID = yield* requireUser;
    const payload = yield* HttpServerRequest.schemaBodyJson(startSchema).pipe(
      Effect.mapError(() => workspaceError("invalid_request", "Invalid request", 400)),
    );
    const volume_dst_path = yield* Effect.try({
      try: () => normalizeVolumePath(payload.volume_dst_path ?? "/home/hacker"),
      catch: (error) => workspaceError("invalid_request", error instanceof Error ? error.message : "Invalid request", 400),
    });
    return yield* ndjsonStream((emit) => startWorkspaceWorkflow(userUUID, { ...payload, volume_dst_path }, emit));
  })),
  HttpRouter.add("POST", "/api/workspaces/stop", Effect.gen(function*() {
    const userUUID = yield* requireUser;
    return HttpServerResponse.jsonUnsafe(yield* stopWorkspaceWorkflow(userUUID));
  })),
);
