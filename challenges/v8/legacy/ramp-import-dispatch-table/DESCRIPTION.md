A Wasm import call crosses from Wasm into JavaScript through import dispatch state.
An exploit can redirect that state without replacing the original JavaScript binding.

In this level, the harness builds a real Wasm import caller and keeps the safe import object unchanged.
Patch the dispatch target so the Wasm call reaches the win import, then run `/challenge/run` with your solve file to get the flag.
