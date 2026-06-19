Custom descriptors are Wasm heap objects that describe other Wasm heap types.
A described type cannot be instantiated on its own; the constructor needs the descriptor object for that type.

In this level, the harness builds a real custom-descriptor Wasm module.
Create the descriptor object, use it to create the described value, return both objects, and run `/challenge/run` with your solve file to get the flag.
