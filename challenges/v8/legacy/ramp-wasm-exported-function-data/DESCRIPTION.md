Exported Wasm functions carry metadata that points from the JavaScript function object back to Wasm function data.
Escape chains often need to follow that metadata before they know which boundary state to corrupt.

This is a metadata-chain preflight, not a memory-corruption primitive.
It isolates the object path used by the later Wasm call-target escape.

In this level, follow the modeled `JSFunction -> SharedFunctionInfo -> WasmExportedFunctionData` chain and retarget the function data to the win call target.
Then run `/challenge/run` with your solve file to get the flag.
