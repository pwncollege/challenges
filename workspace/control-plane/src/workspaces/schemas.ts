import { z } from "zod";

export const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const RESERVED_VOLUME_PATHS = ["/bin", "/boot", "/dev", "/etc", "/proc", "/run", "/sbin", "/sys", "/usr", "/var"];

export const startSchema = z.object({
  node_uuid: z.string().regex(UUID_RE),
  volume_dst_path: z.string().optional(),
  runtime_config: z.object({
    container_image_ref: z.string().min(1),
    entrypoint: z.array(z.string()).optional(),
    env: z.record(z.string(), z.string()).optional(),
  }),
});

export type StartWorkspaceRequest = z.infer<typeof startSchema>;

export function normalizeVolumePath(path: string) {
  if (!path.startsWith("/")) throw new Error("volume_dst_path must be absolute");
  const normalized = new URL(`file://${path}`).pathname.replace(/\/+$/, "") || "/";
  if (normalized !== path.replace(/\/+$/, "")) throw new Error("volume_dst_path must be normalized");
  if (normalized === "/") throw new Error("volume_dst_path cannot be /");
  if (RESERVED_VOLUME_PATHS.some((reserved) => normalized === reserved || normalized.startsWith(`${reserved}/`))) {
    throw new Error("volume_dst_path targets a node-reserved path");
  }
  return normalized;
}
