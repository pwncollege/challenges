Most integer fields in a WebAssembly binary are encoded as unsigned LEB128, not fixed-width little-endian integers.
The same numeric value can occupy a different number of bytes depending on its high bits.

In this level, the harness supplies the numeric fields for a small Wasm module in `fields`.
Define `fill()` to return an object containing unsigned LEB128 byte arrays.
Encode each provided field under the same key: `typeSectionSize`, `functionSectionSize`, `functionTypeIndex`, `exportSectionSize`, `exportNameLength`, `exportFunctionIndex`, `codeSectionSize`, and `codeBodySize`.
Then run `/challenge/run` with your solve file to get the flag.
