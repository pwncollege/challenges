import { Cause, Effect } from "effect";
import { HttpServerResponse } from "effect/unstable/http";
import { WorkerContext } from "../common.ts";
import { workspaceErrorDetails, type WorkspaceError } from "./errors.ts";
import type { WorkspaceEvent } from "./schemas.ts";

export type Emit = (event: WorkspaceEvent) => Effect.Effect<void>;

export const ndjsonStream = Effect.fn("ndjsonStream")(function*<R>(
  run: (emit: Emit) => Effect.Effect<void, WorkspaceError, R>,
) {
  const ctx = yield* WorkerContext;
  const services = yield* Effect.context<R>();
  const encoder = new TextEncoder();
  let connected = true;
  let output!: ReadableStreamDefaultController<Uint8Array>;
  const stream = new ReadableStream<Uint8Array>({
    start(controller) { output = controller; },
    cancel() { connected = false; },
  });
  // Only a handful of status events are emitted. Don't let client backpressure
  // hold a workspace claim, or a disconnected reader roll back a successful start.
  const emit: Emit = (event) => Effect.sync(() => {
    if (connected) output.enqueue(encoder.encode(`${JSON.stringify(event)}\n`));
  });
  ctx.waitUntil(Effect.runPromiseWith(services)(run(emit).pipe(
    Effect.catchCause((cause) => {
      const error = workspaceErrorDetails(Cause.squash(cause));
      return emit({ event: "error", ...error });
    }),
    Effect.ensuring(Effect.sync(() => { if (connected) output.close(); })),
  )));
  return HttpServerResponse.fromWeb(new Response(stream, {
    headers: { "content-type": "application/x-ndjson", "cache-control": "no-cache" },
  }));
});
