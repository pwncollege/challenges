`WebAssembly.Table` objects carry a sandboxed `trusted_dispatch_table` handle.
The handle is still a caged field on the table object, but it names dispatch metadata that later Wasm call paths trust.

In this level, the harness gives you two real `WebAssembly.Table` objects and guarded caged access only to their dispatch-handle fields.
Leak both table addresses, read the donor handle, copy it into the recipient handle field, and run `/challenge/run` with your solve file to get the flag.
