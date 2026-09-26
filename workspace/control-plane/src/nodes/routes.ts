import { Effect } from "effect";
import { HttpRouter, HttpServerRequest, HttpServerResponse } from "effect/unstable/http";
import { Environment } from "../common.ts";
import { fromPromise } from "../workspaces/errors.ts";
import { WorkspaceStore } from "../workspaces/store.ts";
import { sessionUserUUID } from "../session.ts";

export const NodeRoutes = HttpRouter.add("GET", "/api/nodes", Effect.gen(function*() {
  const env = yield* Environment;
  const store = yield* WorkspaceStore;
  const request = yield* HttpServerRequest.HttpServerRequest;
  const userUUID = yield* fromPromise(() => sessionUserUUID(env, request.headers.cookie));
  return HttpServerResponse.jsonUnsafe(yield* store.listNodes(userUUID));
}));
