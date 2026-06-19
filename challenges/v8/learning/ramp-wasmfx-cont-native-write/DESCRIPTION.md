After the continuation read, the same forged-reference shape can be used for a write continuation pair.
The write path stores a 32-bit value through a field access on the forged box reference.
That gives the same absolute 32-bit process-memory write shape used by the native-finish ramps.
The forged-reference helper carries the field-address-to-reference conversion from the read level.

In this level, the harness gives you the already-taught leak as `leakProofBoxPointer()`.
Create the write continuation pair with `makeWriteStaticBox()` and `makeWriteActualBox()`.
Repeat the real continuation-reference swap on that pair with guarded `Sandbox.MemoryView`.
Use `proofFieldAddressFromTaggedBoxPointer(leakedProofBoxPointer)` to target the proof field.
Pass that address through `forgedReferenceForFieldAddress(address)` and mutate the proof field with `resumeWrite(staticBox, forgedReference, expectedToken)`.
Run `/challenge/run` with your solve file to get the flag.
