import { Hono } from "hono";
import type { App } from "./common.ts";
import { registerAuthRoutes } from "./auth/routes.ts";
import { registerNodeRoutes } from "./nodes/routes.ts";
import { registerVolumeRoutes } from "./volumes/routes.ts";
import { registerWorkspaceRoutes } from "./workspaces/routes.ts";

const app = new Hono<App>();

app.get("/", (c) => c.json({ service: "workspace-control-plane" }));

registerAuthRoutes(app);
registerNodeRoutes(app);
registerWorkspaceRoutes(app);
registerVolumeRoutes(app);

export default app;
