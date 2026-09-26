import { Data, Effect } from "effect";

export type WorkspaceErrorDetails = {
  code: string;
  message: string;
  status: number;
};

export class WorkspaceError extends Data.TaggedError("WorkspaceError")<WorkspaceErrorDetails & { cause?: unknown; operationStarted?: boolean }> {}

export function workspaceError(code: string, message = code, status = 500, cause?: unknown) {
  return new WorkspaceError({ code, message, status, cause });
}

// Adapt the native D1, R2, and Web Crypto APIs at the edge of the Effect program.
export function fromPromise<A>(run: () => Promise<A>) {
  return Effect.tryPromise({
    try: run,
    catch: (cause) => cause instanceof WorkspaceError
      ? cause
      : workspaceError("internal_error", cause instanceof Error ? cause.message : "Internal error", 500, cause),
  });
}

export function workspaceErrorDetails(error: unknown): WorkspaceErrorDetails {
  if (error instanceof WorkspaceError) {
    return { code: error.code, message: error.message, status: error.status };
  }
  if (error instanceof Error) {
    return { code: "internal_error", message: error.message || "Internal error", status: 500 };
  }
  return { code: "internal_error", message: "Internal error", status: 500 };
}

export function contentfulStatus(status: number, fallback = 500): number {
  switch (status) {
    case 400:
    case 401:
    case 403:
    case 404:
    case 409:
    case 411:
    case 423:
    case 500:
    case 502:
    case 503:
      return status;
    default:
      return fallback;
  }
}
