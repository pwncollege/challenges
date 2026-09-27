import { Context } from "effect";

export type Bindings = {
  DB: D1Database;
  VOLUMES: R2Bucket;
  PWN_WORKSPACE_R2_BUCKET_URL: string;
  PWN_WORKSPACE_R2_ACCESS_KEY_ID: string;
  PWN_WORKSPACE_R2_SECRET_ACCESS_KEY: string;
  PWN_WORKSPACE_ENVIRONMENT: "development" | "staging" | "production";
  PWN_WORKSPACE_ORIGIN: string;
  PWN_WORKSPACE_PRIVATE_KEY_B64: string;
  PWN_WORKSPACE_PUBLIC_KEY_B64: string;
};

export class Environment extends Context.Service<Environment, Bindings>()("control-plane/Environment") {}
export class WorkerContext extends Context.Service<WorkerContext, ExecutionContext>()("control-plane/WorkerContext") {}

export function unixSeconds() {
  return Math.floor(Date.now() / 1000);
}

export function rows<T>(result: D1Result<unknown>): T[] {
  return result.results as T[];
}
