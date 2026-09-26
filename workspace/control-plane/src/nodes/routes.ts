import type { Hono } from "hono";
import type { App, AppContext } from "../common.ts";
import { rows } from "../common.ts";
import { sessionUserUUID } from "../session.ts";

type ActiveNodeRow = {
  node_uuid: string;
  base_url: string;
};

type HomeNodeRow = {
  node_uuid: string | null;
  base_url: string | null;
};

export function registerNodeRoutes(app: Hono<App>) {
  app.get("/api/nodes", handleNodeList);
}

async function handleNodeList(c: AppContext) {
  const userUUID = await sessionUserUUID(c.env, c.req.header("cookie"));
  const activeNodes = c.env.DB.prepare(
    `SELECT node_uuid, base_url
     FROM nodes
     WHERE status = 'active'
     ORDER BY node_id`,
  );

  if (!userUUID) {
    const result = await activeNodes.all<ActiveNodeRow>();
    return c.json({ nodes: result.results ?? [] });
  }

  const results = await c.env.DB.batch([
    activeNodes,
    c.env.DB.prepare(
      `SELECT n.node_uuid, n.base_url
         FROM users u
         JOIN user_home_volumes uhv
           ON uhv.user_id = u.user_id
         JOIN volumes v
           ON v.volume_id = uhv.volume_id
         LEFT JOIN nodes n
           ON n.node_id = v.node_id
         WHERE u.user_uuid = ?`,
    ).bind(userUUID),
  ]);
  const homeNode = rows<HomeNodeRow>(results[1])[0];
  return c.json({
    nodes: rows<ActiveNodeRow>(results[0]).map((node) => ({
      node_uuid: node.node_uuid,
      base_url: node.base_url,
    })),
    current_home_node: homeNode?.node_uuid && homeNode.base_url
      ? {
          node_uuid: homeNode.node_uuid,
          base_url: homeNode.base_url,
        }
      : null,
  });
}
