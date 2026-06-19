V8 does not store every value as a plain process pointer.
Heap objects are aligned, so their low address bits are normally unused.
V8 uses those low bits as tags that distinguish heap-object references from immediate small integers.

For the compressed heap-object references used in this module, the low tag bit is `1`.
The untagged object start is therefore the leaked reference minus `1`.
That distinction matters because the previous level's cage offset was the start of the object, not the tagged reference value.

In this level, `allocateProofObject()` returns a normal JavaScript object.
`leakTaggedReference(proofObject)` provides the kind of tagged reference leak a first-stage bug would hand you.
The guarded Sandbox still allows `Sandbox.getSizeOf(proofObject)` and a proof-field `Sandbox.MemoryView`, but direct `Sandbox.getAddressOf` is disabled.
Subtract the heap-object tag to recover the object's starting offset, then reduce the write to the previous level's proof-field update.
Use the same guarded `Sandbox.MemoryView` write to store `expectedToken`, then run `/challenge/run` with your solve file to get the flag.
