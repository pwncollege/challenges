import type { ContentfulStatusCode } from "hono/utils/http-status";

export type WorkspaceErrorDetails = {
  code: string;
  message: string;
  status: ContentfulStatusCode;
};

export class WorkspaceError extends Error {
  constructor(
    public readonly code: string,
    message = code,
    public readonly status: ContentfulStatusCode = 500,
    options?: ErrorOptions,
  ) {
    super(message, options);
  }
}

export function workspaceError(code: string, message = code, status: ContentfulStatusCode = 500, cause?: unknown) {
  return new WorkspaceError(code, message, status, cause === undefined ? undefined : { cause });
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

export function contentfulStatus(status: number, fallback: ContentfulStatusCode = 500): ContentfulStatusCode {
  switch (status) {
    case 400:
    case 401:
    case 403:
    case 404:
    case 409:
    case 423:
    case 500:
    case 502:
    case 503:
      return status;
    default:
      return fallback;
  }
}
