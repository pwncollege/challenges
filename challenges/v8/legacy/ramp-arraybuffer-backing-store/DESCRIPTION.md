ArrayBuffer and Wasm memory views read and write through a backing store.
If an escape retargets that backing store to process memory, ordinary view operations become process-memory operations.

This is a post-corruption preflight.
The retargeting ability is provided; the concept is using the retargeted backing store correctly.

In this level, retarget the provided view to the scratch process address and write the token through the view.
Then run `/challenge/run` with your solve file to get the flag.
