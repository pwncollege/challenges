First-stage bugs rarely hand you the same read/write interface.
Before composing stages, normalize the primitive shape so the next stage can use one stable contract.

Pointer compression is the separate V8 optimization that stores many heap references as 32-bit values inside a pointer-compression cage.
For a heap-object reference, that 32-bit value is a cage-relative offset with the normal V8 tag bits still present.
After you untag a heap-object reference, the remaining value is the object's offset inside the cage, not an arbitrary process address.

In this level, the harness gives you two differently shaped caged primitives as `api.primitiveA` and `api.primitiveB`.
Both primitives are backed by guarded writes to real V8 heap fields.
Return `read32(which, offset)` and `write32(which, offset, value)` helpers.
Both helpers should take cage byte offsets; `api.primitiveB` uses 8-byte slot indexes internally, so normalize that shape behind your interface.
Then run `/challenge/run` with your solve file to get the flag.
