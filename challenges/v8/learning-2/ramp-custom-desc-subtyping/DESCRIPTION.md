Custom descriptor types and the heap types they describe form matching subtype chains.
A descriptor for a derived type is not just a random descriptor object; it is the descriptor side of that derived heap type.

In this level, the harness builds a real custom-descriptor Wasm module with a base type and a derived type.
Create the derived descriptor, create the derived value from it, pass both through the base-typed check, and run `/challenge/run` with your solve file to get the flag.
