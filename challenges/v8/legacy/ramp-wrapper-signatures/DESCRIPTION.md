Wrapper signatures decide whether values are preserved or truncated at the Wasm boundary.
For 64-bit values, taking the wrong path silently loses the high bits.

In this level, the harness builds real narrow and wide Wasm wrapper paths.
Choose the path that preserves the full token, then run `/challenge/run` with your solve file to get the flag.
