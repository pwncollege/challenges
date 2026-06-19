WasmFX continuations carry the function state that `resume` will run.
The continuation box stores a sandboxed reference to that continuation object.
In the vulnerable continuation-signature path, two different continuation shapes can share compatible signature metadata, so the static `resume` path accepts the wrong continuation reference.

In this level, the harness gives you `makeStaticContinuationBox()` and `makeActualContinuationBox()` callbacks that allocate two real WasmFX continuation boxes.
Use guarded `Sandbox.MemoryView` to find the tagged continuation-reference field and replace the static box's continuation reference with the actual box's continuation reference.
Call `resumeContinuation(staticBox)`, store the returned token in `resumeToken`, and run `/challenge/run` with your solve file to get the flag.
