import type { Hono } from "hono";
import type { App } from "../common.ts";
import { jsonError } from "../common.ts";
import { committedSnapshotKey, stagingSnapshotKey, storeSnapshotStream } from "../storage.ts";
import { verifyTransferURL } from "./transfers.ts";

export function registerVolumeRoutes(app: Hono<App>) {
  app.get("/api/volumes/:volumeUUID/snapshots/:snapshotUUID", async (c) => {
    if (!(await verifyTransferURL(c, "GET"))) {
      return jsonError(c, 401, "invalid_signature", "Invalid transfer signature");
    }
    const object = await c.env.VOLUMES.get(committedSnapshotKey(c.req.param("volumeUUID"), c.req.param("snapshotUUID")));
    if (!object) return jsonError(c, 404, "snapshot_not_found", "Snapshot not found");
    return new Response(object.body);
  });

  app.put("/api/volumes/:volumeUUID/snapshots/:snapshotUUID", async (c) => {
    if (!(await verifyTransferURL(c, "PUT"))) {
      return jsonError(c, 401, "invalid_signature", "Invalid transfer signature");
    }
    const uploadUUID = c.req.query("upload_uuid");
    if (!uploadUUID) return jsonError(c, 400, "invalid_request", "Missing upload UUID");
    if (!c.req.raw.body) return jsonError(c, 400, "invalid_request", "Missing snapshot body");
    const key = stagingSnapshotKey(c.req.param("volumeUUID"), c.req.param("snapshotUUID"), uploadUUID);
    await storeSnapshotStream(c.env.VOLUMES, key, c.req.raw.body);
    return c.json({ key, uploaded: true });
  });
}
