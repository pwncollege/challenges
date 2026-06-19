Wasm indirect calls resolve through a table entry selected by dispatch state.
The call path is real WebAssembly even when the table entry is changed from JavaScript.

In this level, the harness builds a Wasm module with a real `call_indirect` and a real `WebAssembly.Table`.
Patch the dispatch slot to point at the win function, then run `/challenge/run` with your solve file to get the flag.
