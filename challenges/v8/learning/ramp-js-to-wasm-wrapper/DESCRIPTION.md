A JS-to-Wasm wrapper carries JavaScript values through a Wasm export boundary.
For reference values, preserving identity is the key behavior.

In this level, the harness builds a real Wasm `externref` echo export.
Pass `api.tokenObject` through `api.instance.exports.echo(...)` and return the same object.
Then run `/challenge/run` with your solve file to get the flag.
