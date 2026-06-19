Modern Wasm first-stage bugs can depend on optimized Wasm code.
The vulnerable path is not the interpreter-shaped JavaScript path, and it is not Liftoff baseline Wasm.

In this level, the harness gives you one exported Wasm function as `api.exports.step`.
It also gives you a guarded `api.forceOptimizedWasm` helper backed by V8's real tier-up intrinsic.
Force that function onto the optimized tier, call it with `api.input`, return the result, then run `/challenge/run` with your solve file to get the flag.
