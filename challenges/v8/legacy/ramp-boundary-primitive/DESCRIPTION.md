A boundary-derived caged primitive can feed the same escape preflight as an in-Wasm primitive.
The adapter is what lets the later escape stage ignore which first-stage bug produced the primitive.

In this level, the harness gives you a boundary-shaped primitive and a preflight contract.
Adapt the primitive to the expected read/write shape, then run `/challenge/run` with your solve file to get the flag.
