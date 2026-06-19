`ref.get_desc` exposes the descriptor associated with a Wasm reference.
The first step is using that operation without losing track of the described value's metadata.

In this level, the harness gives you a described value and a `ref_get_desc` helper.
Extract the descriptor token and return it, then run `/challenge/run` with your solve file to get the flag.
