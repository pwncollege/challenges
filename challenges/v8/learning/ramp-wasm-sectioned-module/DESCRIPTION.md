Raw WebAssembly modules are built from a fixed header followed by typed sections.
Exploit triggers that synthesize Wasm must get that container structure right before any deeper bug path is reachable.

In this level, the harness gives you valid section bodies in `sectionBodies`.
Define `build()` and use the provided `section(id, body)` helper.
Wrap the section bodies into a complete module whose exported `answer` function returns the expected value.
Run `/challenge/run` with your solve file to get the flag.
