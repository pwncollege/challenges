import { Effect, Schema } from "effect";
import { HttpRouter, HttpServerRequest, HttpServerResponse } from "effect/unstable/http";
import { Environment } from "../common.ts";
import { createSessionCookie } from "../session.ts";
import { fromPromise, workspaceError } from "../workspaces/errors.ts";
import { UUID } from "../workspaces/schemas.ts";
import { WorkspaceStore } from "../workspaces/store.ts";

const loginSchema = Schema.Struct({ user_uuid: UUID });

export const AuthRoutes = HttpRouter.add("POST", "/api/login", Effect.gen(function*() {
  const env = yield* Environment;
  const store = yield* WorkspaceStore;
  const payload = yield* HttpServerRequest.schemaBodyJson(loginSchema).pipe(
    Effect.mapError(() => workspaceError("invalid_request", "Invalid request", 400)),
  );
  const user = yield* store.findUser(payload.user_uuid);
  if (!user) return yield* workspaceError("user_not_found", "User not found", 404);
  const cookie = yield* fromPromise(() => createSessionCookie(env, user.user_uuid));
  return HttpServerResponse.jsonUnsafe({ user_uuid: user.user_uuid }, { headers: { "set-cookie": cookie } });
}));
