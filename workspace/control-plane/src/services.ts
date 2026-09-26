import { Context, Effect } from "effect";
import { Environment } from "./common.ts";
import { NodeClient } from "./node-client.ts";
import { SnapshotStore } from "./storage.ts";
import { WorkspaceStore } from "./workspaces/store.ts";

// These constructors only create lazy adapters. Each request gets its own
// bindings and key cache; I/O starts when a service operation is executed.
export const makeServices = Effect.gen(function*() {
  const env = yield* Environment;
  const nodes = yield* NodeClient.make;
  const snapshots = yield* SnapshotStore.make;
  const workspaces = yield* WorkspaceStore.make;
  return Context.make(Environment, env).pipe(
    Context.add(NodeClient, nodes),
    Context.add(SnapshotStore, snapshots),
    Context.add(WorkspaceStore, workspaces),
  );
});
