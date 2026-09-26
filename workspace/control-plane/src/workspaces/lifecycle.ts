import { Effect, Exit, Scope } from "effect";

// Register rollback only after acquisition succeeds. Effect masks interruption
// across acquisition and registration, and runs finalizers in reverse order.
export function rollbackOnFailure<A, E, R, E2, R2>(
  acquire: Effect.Effect<A, E, R>,
  rollback: (value: A) => Effect.Effect<unknown, E2, R2>,
) {
  return Effect.acquireRelease(acquire, (value, exit) => Exit.isFailure(exit)
    ? rollback(value).pipe(Effect.catchCause((cause) => Effect.logWarning("Workspace rollback failed", cause)))
    : Effect.void);
}

export function commitWorkflow<A, E, R, E2, R2>(
  prepare: Effect.Effect<A, E, R>,
  commit: (value: A) => Effect.Effect<unknown, E2, R2>,
) {
  return Effect.scoped(Effect.uninterruptibleMask((restore) => Effect.gen(function*() {
    const rollback = yield* Scope.make();
    yield* Effect.addFinalizer((exit) => Scope.close(rollback, exit));
    const value = yield* restore(Scope.provide(prepare, rollback));
    // D1 releases the claims on commit. Close the rollback scope successfully
    // before accepting interruption, so cleanup cannot touch the next operation.
    yield* commit(value);
    yield* Scope.close(rollback, Exit.void);
    return value;
  })));
}
