import type { Hono } from "hono";
import type { App, AppContext } from "../common.ts";
import { jsonError } from "../common.ts";
import { ndjsonStream } from "./events.ts";
import { workspaceErrorDetails } from "./errors.ts";
import { sessionUserUUID } from "../session.ts";
import { normalizeVolumePath, startSchema } from "./schemas.ts";
import { startWorkspaceWorkflow } from "./start-workflow.ts";
import { stopWorkspaceWorkflow } from "./stop-workflow.ts";

export function registerWorkspaceRoutes(app: Hono<App>) {
  app.post("/api/workspaces/start", handleWorkspaceStart);
  app.post("/api/workspaces/stop", handleWorkspaceStop);
}

async function handleWorkspaceStart(c: AppContext) {
  const userUUID = await sessionUserUUID(c.env, c.req.header("cookie"));
  if (!userUUID) return jsonError(c, 401, "unauthorized", "Login required");

  const parsed = startSchema.safeParse(await c.req.json().catch(() => undefined));
  if (!parsed.success) return jsonError(c, 400, "invalid_request", parsed.error.issues[0]?.message ?? "Invalid request");
  let payload = parsed.data;
  try {
    payload = { ...payload, volume_dst_path: normalizeVolumePath(payload.volume_dst_path ?? "/home/hacker") };
  } catch (error) {
    return jsonError(c, 400, "invalid_request", error instanceof Error ? error.message : "Invalid request");
  }
  return ndjsonStream(c, (emit) => startWorkspaceWorkflow(c.env, userUUID, payload, emit));
}

async function handleWorkspaceStop(c: AppContext) {
  const userUUID = await sessionUserUUID(c.env, c.req.header("cookie"));
  if (!userUUID) return jsonError(c, 401, "unauthorized", "Login required");

  try {
    return c.json(await stopWorkspaceWorkflow(c.env, userUUID));
  } catch (error) {
    const stopError = workspaceErrorDetails(error);
    return jsonError(c, stopError.status, stopError.code, stopError.message);
  }
}
