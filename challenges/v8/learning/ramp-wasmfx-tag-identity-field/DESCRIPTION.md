`WebAssembly.Tag` is a JavaScript wrapper around a sandboxed Wasm exception-tag identity.
When a later Wasm module imports that tag, V8 uses the wrapper's internal tag identity, not just the JavaScript object name.

In this level, the harness gives you two real `WebAssembly.Tag` wrappers with different signatures as `tagA` and `tagB`.
Find the wrapper field that points at each tag identity.
Copy tag A's identity into tag B's wrapper with guarded `Sandbox.MemoryView`.
Run `/challenge/run` with your solve file to get the flag.
