The WasmFX escape ramps end with a primitive shaped as absolute 32-bit native read/write.
The later ELF and return-chain work is easier to express with 64-bit qword helpers.
This pure interface ramp backs those 32-bit operations with a provided loaded-ELF fixture; the capstones supply the real native primitive.

In this level, the harness provides only `api.read32(address)` and `api.write32(address, value)`.
Return `read64` and `write64` helpers that combine two little-endian 32-bit accesses, then run `/challenge/run` with your solve file to get the flag.
