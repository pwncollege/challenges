WebAssembly `externref` table slots store JavaScript object identity, not a printable copy of an object field.
That identity is what later reference-typed Wasm paths rely on.

In this level, the harness gives you a token object and a real `WebAssembly.Table` whose element type is `externref`.
Store `api.tokenObject` in `api.referenceTable` at `api.slot`, then run `/challenge/run` with your solve file to get the flag.
