A Wasm GC struct field can store a reference to another Wasm heap type.
In the binary format, a nullable reference field is encoded as `ref null` followed by the referenced type index.

In this level, define `buildHolderStructType(api)` for a real Wasm module.
The harness already defines the target struct at type index `api.targetTypeIndex`.
Return the bytes for one mutable field that can hold a nullable reference to that target type.
Use the provided constants `api.STRUCT`, `api.REF_NULL`, and `api.MUTABLE`.
Then run `/challenge/run` with your solve file to get the flag.
