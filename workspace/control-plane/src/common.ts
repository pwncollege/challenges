import type { Context } from "hono";
import type { ContentfulStatusCode } from "hono/utils/http-status";

export type Bindings = {
  DB: D1Database;
  VOLUMES: R2Bucket;
  PWN_WORKSPACE_ENVIRONMENT: "development" | "staging" | "production";
  PWN_WORKSPACE_ORIGIN: string;
  PWN_WORKSPACE_PRIVATE_KEY_B64: string;
  PWN_WORKSPACE_PUBLIC_KEY_B64: string;
};

export type App = { Bindings: Bindings };
export type AppContext = Context<App>;

export function jsonError(
  c: AppContext,
  status: ContentfulStatusCode,
  code: string,
  message: string,
  extra: Record<string, unknown> = {},
) {
  return c.json({ error: { code, message, ...extra } }, status);
}

export function unixSeconds() {
  return Math.floor(Date.now() / 1000);
}

export async function one<T>(stmt: D1PreparedStatement): Promise<T | null> {
  return (await stmt.first<T>()) ?? null;
}

export function rows<T>(result: D1Result<unknown>): T[] {
  return result.results as T[];
}
