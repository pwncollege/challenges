Some modern Wasm first-stage bugs corrupt real Wasm GC arrays.
After you can allocate Wasm GC arrays, the next useful property is mutable element storage.
An `array.set` writes a typed element, and a later `array.get` observes that same element.

In this level, the harness gives you a real Wasm module with an `i32` array type as `api.exports`.
It also gives you already-created arrays as `api.smallArray` and `api.largeArray`.
Use `api.exports.arraySet` and `api.exports.arrayGet` at `api.probeIndex`.
Store and read `api.smallValue` and `api.largeValue`.
Return the observed values as `smallValue` and `largeValue`, then run `/challenge/run` with your solve file to get the flag.
