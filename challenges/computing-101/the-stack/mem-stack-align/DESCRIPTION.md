You've now seen `argc`, `argv`, and `envp` on the stack.
But here's a deeper truth: **where each piece of data lives on the stack is not fixed --- it depends on how the program is launched.**

When the kernel sets up the stack at `exec` time, it places all the strings (the program name, the arguments, and the environment variables) at the top of the stack region, and then computes the `argv[i]` and `envp[i]` pointers to point into that string region.
If you change the environment (e.g., add `env -i FOO=xxxxx`), the cumulative env-string region grows, and the value of `argv[0]` (the address it points to) shifts to follow.

We've turned address-space-layout randomization (ASLR) off for this challenge so that addresses are deterministic --- the same launch always produces the same `argv[0]`.

`/challenge/program`:

1. Requires `argc == 1` (no extra arguments).
2. Reads `argv[0]` from the stack.
3. Hands you the flag *if and only if* `(argv[0] & 0xFFFF) == 0x5390`.

Your job: launch it once with a clean environment (`env -i /challenge/program`) and observe what `argv[0]` currently is.
Then add an environment variable and watch the value shift.
Tune the *length* of your environment variable (e.g., `env -i FOO=xxxxx /challenge/program`) until the low 16 bits of `argv[0]` are `0x5390`.

The lesson: you control your program's stack layout not by changing the program, but by changing **how it's launched**.
