The 452605803 escape uses corrupted Wasm dispatch state to reach imported-wrapper signature metadata.
Before the helper module's absolute read path works, the exploit copies the live signature state from the source wrapper slot to the destination wrapper slot.

In this level, the harness prepares the real dispatch state and exposes only the resulting `sigRead`, `sigWrite`, and `read64` operations.
Copy the signature state from offset `0x30` to offset `0x28`, return `read64(probeAddress)`, and run `/challenge/run` with your solve file to get the flag.
