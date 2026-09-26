import type { AppContext } from "../common.ts";
import { workspaceErrorDetails } from "./errors.ts";

export type Emit = (event: unknown) => Promise<void>;

export function ndjsonStream(c: AppContext, run: (emit: Emit) => Promise<void>) {
  const stream = new TransformStream();
  const writer = stream.writable.getWriter();
  const encoder = new TextEncoder();
  const emit: Emit = async (event) => {
    await writer.write(encoder.encode(`${JSON.stringify(event)}\n`));
  };

  c.executionCtx.waitUntil(
    (async () => {
      try {
        await run(emit);
      } catch (error) {
        const streamError = workspaceErrorDetails(error);
        await emit({
          event: "error",
          code: streamError.code,
          message: streamError.message,
          status: streamError.status,
        });
      } finally {
        await writer.close();
      }
    })(),
  );

  return new Response(stream.readable, {
    headers: {
      "content-type": "application/x-ndjson",
      "cache-control": "no-cache",
    },
  });
}
