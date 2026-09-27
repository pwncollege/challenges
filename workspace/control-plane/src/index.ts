import { Context, Effect, Layer } from "effect";
import { HttpRouter, HttpServer, HttpServerResponse } from "effect/unstable/http";
import { Environment, WorkerContext, type Bindings } from "./common.ts";
import { AuthRoutes } from "./auth/routes.ts";
import { NodeRoutes } from "./nodes/routes.ts";
import { WorkspaceRoutes } from "./workspaces/routes.ts";
import type { WorkspaceError } from "./workspaces/errors.ts";
import { makeServices } from "./services.ts";

const Errors = HttpRouter.middleware<{ handles: WorkspaceError }>()((http) => http.pipe(
  Effect.catchTag("WorkspaceError", ({ code, message, status }) =>
    Effect.succeed(HttpServerResponse.jsonUnsafe({ error: { code, message } }, { status }))),
));

export const { handler } = HttpRouter.toWebHandler(Layer.mergeAll(
  HttpRouter.add("GET", "/", HttpServerResponse.jsonUnsafe({ service: "workspace-control-plane" })),
  AuthRoutes, NodeRoutes, WorkspaceRoutes,
).pipe(Layer.provide(Errors.layer), Layer.provide(HttpServer.layerServices)), { disableLogger: true });

export default {
  fetch(request: Request, env: Bindings, ctx: ExecutionContext) {
    const services = Effect.runSync(makeServices.pipe(Effect.provideService(Environment, env)));
    return handler(request, Context.add(services, WorkerContext, ctx));
  },
} satisfies ExportedHandler<Bindings>;
