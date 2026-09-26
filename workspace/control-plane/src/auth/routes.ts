import type { Hono } from "hono";
import { z } from "zod";
import type { App, AppContext } from "../common.ts";
import { jsonError, one } from "../common.ts";
import { createSessionCookie } from "../session.ts";
import { UUID_RE } from "../workspaces/schemas.ts";

const loginSchema = z.object({
  user_uuid: z.string().regex(UUID_RE),
});

export function registerAuthRoutes(app: Hono<App>) {
  app.post("/api/login", handleLogin);
}

async function handleLogin(c: AppContext) {
  const parsed = loginSchema.safeParse(await c.req.json().catch(() => undefined));
  if (!parsed.success) return jsonError(c, 400, "invalid_request", "Invalid request");

  const user = await one<{ user_uuid: string }>(
    c.env.DB.prepare("SELECT user_uuid FROM users WHERE user_uuid = ?").bind(parsed.data.user_uuid),
  );
  if (!user) return jsonError(c, 404, "user_not_found", "User not found");

  return c.json(
    { user_uuid: user.user_uuid },
    {
      headers: {
        "set-cookie": await createSessionCookie(c.env, user.user_uuid),
      },
    },
  );
}
