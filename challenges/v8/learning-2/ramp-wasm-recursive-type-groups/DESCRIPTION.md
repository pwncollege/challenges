Wasm heap types can be defined in a recursive type group.
That matters when related types refer to each other.
The validator must see the group as one connected definition rather than as unrelated standalone types.

In this level, define `buildRecursiveGroup(api)` for a real Wasm module.
The harness provides `api.leftSubtype` and `api.rightSubtype`, which are the two mutually referencing struct subtype definitions.
Return one recursive group entry that contains both provided subtype definitions.
Use the provided `api.REC` constant for the group wrapper.
Then run `/challenge/run` with your solve file to get the flag.
