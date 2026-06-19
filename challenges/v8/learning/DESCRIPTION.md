This module teaches modern two-stage V8 heap-sandbox escape chains.
The active challenges are one-concept ramp levels followed by a 2026 WasmFX capstone spine.

V8's heap sandbox places many V8 heap objects inside a reserved address range called the heap cage.
A cage-local primitive can operate on objects inside that range.
It cannot directly read or write arbitrary process memory outside it.

The ramp challenges isolate the pieces of those chains one concept at a time.
They start with cage-local primitives, Wasm byte encoding, recursive type groups, Wasm reference state, and boundary wrappers.
They then ramp from optimized Wasm execution and stale array effects to a standalone CVE-2026-7899 caged write.
From there, they teach the issue 514157844 imported-tag escape and the native process-memory finish before the first full chain.
After that first capstone, the module ramps through the real CVE-2026-9973 trigger, bridge discovery, `addrof`, and caged read/write before using it in the second chain.
Finally, the module introduces the issue 505751230 continuation escape swap and immediately uses it in the final chain.
