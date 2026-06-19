JavaScript objects can be stored as Wasm reference values.
That storage should preserve object identity rather than copying a primitive field.

In this level, the harness gives you a mutable Wasm `externref` global and a token object.
Store `api.tokenObject` in `api.wasmGlobal.value`, then run `/challenge/run` with your solve file to get the flag.
