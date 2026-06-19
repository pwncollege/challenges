A descriptor is metadata that tells code how to interpret a value.
In this ramp, `api.value.descriptor` tells the value's proof method which target object to use.

Descriptor confusion is a type confusion where the value stays the same, but code follows the wrong descriptor for that value.
In this level, `api.value` starts with a declared descriptor that selects a decoy target, while `api.confusedDescriptor` selects the proof target.
Use guarded `Sandbox.MemoryView` to retarget `api.value.descriptor` to `api.confusedDescriptor`, then call `api.value.prove()`.

Run `/challenge/run` with your solve file to get the flag.
