This module teaches modern two-stage V8 heap-sandbox escape chains.
The active challenges are one-concept ramp levels followed by a 2026 WasmFX capstone spine.

The flow starts from the final capability and works backward.
First, you practice the native process-memory finish from a provided absolute read/write primitive.
Then, you learn the heap-cage and guarded Sandbox access model that the V8-specific ramps use.
After that, you use guarded access to study the WasmFX imported-tag escape that turns caged corruption into process-memory access.
Finally, you fill in the Wasm reference, Wasm GC array, and optimized-Wasm concepts needed to produce the caged primitive through a real first-stage bug.

The first full chain uses CVE-2026-7899 for caged read/write and Chromium issue 514157844 for the imported-tag escape.
The next chain swaps the first stage to CVE-2026-9973 while keeping the imported-tag escape.
The final chain keeps CVE-2026-9973 and swaps the escape to Chromium issue 505751230's WasmFX continuation path.
