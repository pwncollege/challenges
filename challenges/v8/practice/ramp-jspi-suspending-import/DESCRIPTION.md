JSPI lets a Wasm call suspend on a JavaScript `Promise` and resume with that promise's value.
That path has two boundary adapters: wrap the Promise-returning JavaScript import with `WebAssembly.Suspending`, then wrap the exported Wasm caller with `WebAssembly.promising`.

In this level, the harness gives you a real Wasm function that calls a JavaScript import returning the token promise.
Build the two JSPI adapters, call the promising export, return the resolved token object, and run `/challenge/run` with your solve file to get the flag.
