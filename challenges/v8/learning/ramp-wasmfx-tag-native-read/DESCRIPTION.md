After the imported-tag leak, the exploit has a tagged pointer to a proof box.
The native read path takes the target field address and reads through the confused imported-tag signature.
That gives the absolute 32-bit process-memory read shape used by the native-finish ramps.
This level keeps the pointer arithmetic helperized so the new concept is the imported-tag read effect.

In this level, repeat the guarded tag identity field copy before calling `leakProofBoxPointer()`.
Use `proofFieldAddressFromTaggedBoxPointer(leakedProofBoxPointer)` to target the proof field.
Read that field with `nativeRead32(address)` and store the result in `readProofValue`.
Run `/challenge/run` with your solve file to get the flag.
