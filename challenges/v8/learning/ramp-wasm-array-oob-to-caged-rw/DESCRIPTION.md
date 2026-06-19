After a Wasm array-corruption first stage expands a real Wasm GC array, array elements become a caged heap access surface.
The useful exploit shape is not "write element N"; it is `read32(offset)` and `write32(offset, value)` over cage byte offsets.

In this level, the harness gives you a real Wasm i32 array, two normal JavaScript proof objects, and guarded `Sandbox` access.
Guarded `Sandbox.getAddressOf` and `Sandbox.getSizeOf` are available for the array and both proof objects, but `Sandbox.MemoryView` is limited to the original array object.
Use that `MemoryView` access to find and expand the array's real length word.
Then define global `read32(offset)` and `write32(offset, value)` helpers over cage byte offsets by converting those offsets into the real Wasm `array.get` and `array.set` element indexes.
Run `/challenge/run` with your solve file to get the flag.
