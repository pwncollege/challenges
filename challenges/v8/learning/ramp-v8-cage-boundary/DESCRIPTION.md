V8's heap sandbox places many V8 heap objects inside a reserved address range called the heap cage.
A cage-local primitive can read or write inside that range, but it cannot directly read or write arbitrary process memory outside it.

Modern V8 exploits often start with a cage-local primitive as the first vulnerability in an exploit chain.
That is useful, but it is not the same thing as process-wide memory access.

This level will model the effect of such a vulnerability.
In this level, the harness gives you `allocateProofObject()` for a normal JavaScript object.
It also gives you guarded access to V8's official `Sandbox.getAddressOf`, `Sandbox.getSizeOf`, and `Sandbox.MemoryView` APIs.
`Sandbox.getAddressOf(proofObject)` gives the heap-cage offset of the start of the V8 heap object, including its header and other object metadata.
`Sandbox.getSizeOf(proofObject)` gives the full object size in bytes.
The proof object has one 32-bit proof field, and that V8 metadata comes before the field.
In this harness, that field occupies the final 4 bytes of the object, so its offset (within the heap cage) is the object offset plus the object size minus 4.
Write `expectedToken` to that field through a guarded `Sandbox.MemoryView`, then run `/challenge/run` with your solve file to get the flag.
