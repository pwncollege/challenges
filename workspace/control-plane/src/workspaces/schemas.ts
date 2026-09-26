import { Schema } from "effect";

export const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const RESERVED_VOLUME_PATHS = ["/bin", "/boot", "/dev", "/etc", "/proc", "/run", "/sbin", "/sys", "/usr", "/var"];

export const UUID = Schema.String.check(Schema.isPattern(UUID_RE));

export const RuntimeConfig = Schema.Struct({
  container_image_ref: Schema.NonEmptyString,
  entrypoint: Schema.optionalKey(Schema.Array(Schema.String)),
  env: Schema.optionalKey(Schema.Record(Schema.String, Schema.String)),
});
export type RuntimeConfig = typeof RuntimeConfig.Type;

export const startSchema = Schema.Struct({
  node_uuid: UUID,
  volume_dst_path: Schema.optionalKey(Schema.String),
  runtime_config: RuntimeConfig,
});

export type StartWorkspaceRequest = typeof startSchema.Type;

export const NodeStartRequest = Schema.Struct({
  runtime_config: RuntimeConfig,
  volume: Schema.Struct({ volume_uuid: UUID, dst_path: Schema.String }),
});
export type NodeStartRequest = typeof NodeStartRequest.Type;

export const NodeErrorResponse = Schema.Struct({
  error: Schema.Struct({ code: Schema.NonEmptyString, message: Schema.String }),
});

export const WorkspaceEvent = Schema.Union([
  Schema.Struct({
    event: Schema.Literal("status"),
    phase: Schema.Literals(["claiming", "stopping_existing_workspace", "reclaiming_volume", "activating_volume", "starting"]),
    message: Schema.String,
  }),
  Schema.Struct({ event: Schema.Literal("complete"), workspace_uuid: UUID, url: Schema.String }),
  Schema.Struct({ event: Schema.Literal("error"), code: Schema.String, message: Schema.String, status: Schema.Int }),
]);
export type WorkspaceEvent = typeof WorkspaceEvent.Type;

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
