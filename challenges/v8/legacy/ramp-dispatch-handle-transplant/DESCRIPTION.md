Once a useful Wasm table target exists, an exploit often needs to transplant it into another call path.
The important operation is preserving the callable entry, not recomputing the target from scratch.

In this level, the harness gives you donor and recipient `WebAssembly.Table` objects.
Move the donor's callable entry into the recipient and prove it through the recipient call path, then run `/challenge/run` with your solve file to get the flag.
