Irregexp records capture groups as start and end offsets while it executes a regular expression.
JavaScript normally gives you the captured string, but the `d` flag also exposes those offsets through match indices.

This matters because the later Irregexp escape corrupts RegExp state and relies on where execution writes register-like match state.

In this level, match the token in the provided subject string with a real RegExp capture group.
Return the captured token and that capture's start and end offsets, then run `/challenge/run` with your solve file to get the flag.
