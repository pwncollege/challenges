A descriptor confusion is useful when you can make the wrong descriptor expose data that the correct descriptor would not expose.
One common target for that first useful value is a tagged heap-object reference.

This level still avoids Wasm and models that post-confusion leak directly.
`allocateProofObject()` returns a normal JavaScript object.
`leakWithDescriptor(proofObject, confusedDescriptor)` models the bug using the wrong descriptor and returns the object's tagged reference.
Untag the reference, derive the proof-field offset, update the field with guarded `Sandbox.MemoryView`, then run `/challenge/run` with your solve file to get the flag.
