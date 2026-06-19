Some modern Wasm first-stage bugs corrupt real Wasm GC arrays.
Before using those arrays as an exploitation surface, you need to create real arrays and observe their runtime length.

In this level, the harness gives you a real Wasm module with an `i32` array type as `api.exports`.
Use `api.exports.newArray` and `api.exports.arrayLen` to create arrays of length `api.smallLength` and `api.largeLength`.
Return both observed lengths as `smallLength` and `largeLength`, then run `/challenge/run` with your solve file to get the flag.
