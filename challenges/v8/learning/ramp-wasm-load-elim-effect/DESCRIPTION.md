The Wasm load-elimination first-stage family is useful because optimized code can keep using an older Wasm array reference after normal state has moved on.
The result is a stale write: the holder points at one array, but the write lands in the earlier array.

In this level, guarded `Sandbox` access stands in for the first-stage corruption, but the objects are real Wasm GC arrays and a real Wasm holder struct.
Create stale and current arrays with `api.staleLength` and `api.currentLength`.
Use `api.holderMarker`, `api.probeIndex`, `api.initialCurrentValue`, and `api.staleWriteValue` as the probe inputs.
Create the holder while it points at the current array, then use guarded `Sandbox.MemoryView` to replace the holder's array-reference field with the tagged stale-array reference.
Invoke `api.exports.holderSet` through that corrupted holder.
Return `holderLength`, `currentValue`, `staleValue`, and `marker` to prove the stale array changed while the current array did not.
Run `/challenge/run` with your solve file to get the flag.
