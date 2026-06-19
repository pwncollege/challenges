Type confusion is a layout problem.
Code writes through the field layout for one type while the object in memory actually has another type.

In this level, `allocateProofObject()` returns the proof object.
`allocateReferenceCell()` returns a frozen cell whose `target` starts out pointing at a decoy object.
The cell has one field, so after the object header its final 32-bit slot holds the tagged reference for `target`.
The guarded Sandbox allows addresses for `proofObject` and `referenceCell`, sizing for `referenceCell`, and a `Sandbox.MemoryView` over that target slot.
You have already seen the heap-object tag bit: object-reference slots hold the tagged reference value, not the untagged object start.
Use guarded `Sandbox.MemoryView` to retarget that object-reference slot to `proofObject`, then call `referenceCell.prove()`.

Run `/challenge/run` with your solve file to get the flag.
