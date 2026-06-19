Custom descriptors also participate in runtime reference checks.
A descriptor-checked cast compares the object against the descriptor supplied to the instruction, so two unrelated descriptor/described pairs can take different branch paths even when both are ordinary Wasm GC references.

In this level, the harness builds a real custom-descriptor Wasm module with a left pair and a right pair.
Create both values, classify each value with both descriptor-checked classifiers, and run `/challenge/run` with your solve file to get the flag.
