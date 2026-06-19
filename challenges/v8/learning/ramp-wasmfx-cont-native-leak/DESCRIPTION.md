The continuation-reference swap from the previous level is useful because the actual continuation can have a different result shape.
The static resume path still expects the original shape.
One useful shape mismatch returns a Wasm reference as an integer-sized value.

In this level, the harness gives you real WasmFX continuation boxes and guarded `Sandbox` access to those boxes.
Call `initProofBox()`.
Create the leak continuation pair with `makeLeakStaticBox()` and `makeLeakActualBox()`.
Repeat the real continuation-reference swap from the previous level, then resume the static box with `resumeLeak(staticBox)`.
Store the returned tagged proof-box pointer in `leakedProofBoxPointer`.
Run `/challenge/run` with your solve file to get the flag.
