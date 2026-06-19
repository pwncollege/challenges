Growing a WebAssembly table changes which table entries exist and can become callable.
The exploit path needs the live post-growth slot, not a hardcoded pre-growth assumption.

In this level, the harness gives you a real `WebAssembly.Table` and a win function.
Grow the table, record the new live index for the validator, then run `/challenge/run` with your solve file to get the flag.
