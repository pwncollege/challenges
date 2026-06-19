Imported Wasm wrappers are real boundary crossings from Wasm into JavaScript.
Before corrupting one, you should be able to drive the ordinary wrapper path and observe its return value.

In this level, the harness builds a real Wasm module that imports a JavaScript function.
Call the exported Wasm wrapper and return its token, then run `/challenge/run` with your solve file to get the flag.
