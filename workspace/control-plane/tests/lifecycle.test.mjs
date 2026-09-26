import assert from "node:assert/strict";
import test from "node:test";
import { Cause, Effect, Exit, Fiber } from "effect";
import { loadModule } from "./helpers.mjs";

const { commitWorkflow, rollbackOnFailure } = await loadModule("src/workspaces/lifecycle.ts");

for (const [kind, failure] of [["failure", Effect.fail("failed")], ["defect", Effect.die("defect")]]) {
  test(`rollback survives cleanup failures and releases claims last: ${kind}`, async () => {
    const calls = [];
    const exit = await Effect.runPromiseExit(commitWorkflow(Effect.gen(function*() {
      yield* rollbackOnFailure(Effect.void, () => Effect.sync(() => calls.push("claim")));
      yield* rollbackOnFailure(Effect.void, () => Effect.gen(function*() {
        calls.push("container");
        return yield* Effect.fail("cleanup failed");
      }));
      yield* failure;
    }), () => Effect.sync(() => calls.push("commit"))));
    assert.ok(Exit.isFailure(exit));
    assert.deepEqual(calls, ["container", "claim"]);
  });
}

test("a failed acquisition never releases someone else's claim", async () => {
  let released = false;
  const exit = await Effect.runPromiseExit(commitWorkflow(
    rollbackOnFailure(Effect.fail("busy"), () => Effect.sync(() => { released = true; })),
    () => Effect.void,
  ));
  assert.ok(Exit.isFailure(exit));
  assert.equal(released, false);
});

test("interruption during acquisition waits for registration, then rolls back", async () => {
  const acquiring = Promise.withResolvers();
  const acquired = Promise.withResolvers();
  const calls = [];
  const fiber = Effect.runFork(commitWorkflow(rollbackOnFailure(Effect.promise(() => {
    acquiring.resolve();
    return acquired.promise;
  }), () => Effect.sync(() => calls.push("rollback"))), () => Effect.sync(() => calls.push("commit"))));
  await acquiring.promise;
  const interrupted = Effect.runPromise(Fiber.interrupt(fiber));
  assert.deepEqual(calls, []);
  acquired.resolve();
  await interrupted;
  const exit = await Effect.runPromise(Fiber.await(fiber));
  assert.ok(Exit.isFailure(exit) && Cause.hasInterrupts(exit.cause));
  assert.deepEqual(calls, ["rollback"]);
});

test("interruption during D1 commit cannot run rollback after releasing locks", async () => {
  const committing = Promise.withResolvers();
  const committed = Promise.withResolvers();
  const calls = [];
  const fiber = Effect.runFork(commitWorkflow(
    rollbackOnFailure(Effect.void, () => Effect.sync(() => calls.push("rollback"))),
    () => Effect.promise(async () => {
      committing.resolve();
      await committed.promise;
      calls.push("commit");
    }),
  ));
  await committing.promise;
  const interrupted = Effect.runPromise(Fiber.interrupt(fiber));
  committed.resolve();
  await interrupted;
  assert.deepEqual(calls, ["commit"]);
});

test("a failed commit rolls back but a failed completion notification does not", async () => {
  for (const failedCommit of [true, false]) {
    let released = false;
    const exit = await Effect.runPromiseExit(commitWorkflow(
      rollbackOnFailure(Effect.void, () => Effect.sync(() => { released = true; })),
      () => failedCommit ? Effect.fail("commit failed") : Effect.void,
    ).pipe(Effect.andThen(Effect.fail("notification failed"))));
    assert.ok(Exit.isFailure(exit));
    assert.equal(released, failedCommit);
  }
});
