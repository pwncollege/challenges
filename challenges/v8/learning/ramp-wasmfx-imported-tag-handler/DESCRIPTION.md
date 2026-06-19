WasmFX `suspend` and `resume` use exception tags to decide which handler catches a suspension.
For imported tags, the handler match uses the imported tag identity stored in the Wasm instance's tag table.

In this level, repeat the guarded tag identity field copy from the previous ramp.
Instantiate the provided WasmFX probe with `instantiateImportedTagProbe(tagA, tagB)`.
Call its handler path, store the returned value in `handlerToken`, and run `/challenge/run` with your solve file to get the flag.
