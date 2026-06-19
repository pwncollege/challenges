Wasm GC adds heap types such as structs.
In the binary format, a struct type starts with a struct opcode, then a field count, then each field's storage type and mutability byte.

In this level, define `buildStructType(api)` for a real Wasm module.
Return the bytes for one struct with two `i32` fields: the first mutable, the second immutable.
Use the provided constants `api.STRUCT`, `api.I32`, `api.MUTABLE`, and `api.IMMUTABLE`.
Then run `/challenge/run` with your solve file to get the flag.
