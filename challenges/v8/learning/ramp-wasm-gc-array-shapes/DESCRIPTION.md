Some modern Wasm first-stage bugs corrupt holder objects that point at Wasm GC arrays.
A holder struct keeps a reference to one array, and normal Wasm methods follow whichever array reference is currently stored in that field.

In this level, the harness gives you `api.smallArray`, `api.largeArray`, and holder methods in `api.exports`.
Create the holder with `api.exports.makeHolder(api.smallArray, api.holderMarker)`.
Observe `api.probeIndex` through the holder.
Retarget the holder with `api.exports.holderSetArray`, then observe it again.
Return `beforeLength`, `beforeValue`, `afterLength`, `afterValue`, and `marker`, then run `/challenge/run` with your solve file to get the flag.
