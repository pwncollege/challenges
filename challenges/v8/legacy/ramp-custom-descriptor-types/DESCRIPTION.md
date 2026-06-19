Custom descriptors attach metadata to the heap type they describe.
When a bug confuses descriptor validation, the exploit still needs to track which descriptor belongs to which described type.

In this level, the harness gives you a descriptor and lookup functions for its described value and token.
Return the descriptor, the described value, and the descriptor token, then run `/challenge/run` with your solve file to get the flag.
