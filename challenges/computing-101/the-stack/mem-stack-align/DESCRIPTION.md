In the previous levels, you've read `argc`, `argv`, and `envp` from the stack.
But where each of those values *sits* on the stack --- the actual addresses --- depends on **how the program was launched**.

When the kernel sets up the stack at `exec` time, it places all the strings (the program name, the arguments, and the environment variables) at the *top* of the stack region, and then computes the `argv[i]` and `envp[i]` pointers to point into them:

```text
high addresses
  +──────────────────────────+
  │ env strings              │  ◀── "PATH=...\0" "HOME=...\0" ...
  +──────────────────────────+
  │ arg strings              │  ◀── "/challenge/program\0"  (argv[0] points here)
  +──────────────────────────+
  │ auxv                     │
  +──────────────────────────+
  │ envp[]  (pointers)       │
  +──────────────────────────+
  │ argv[]  (pointers)       │
  +──────────────────────────+
  │ argc                     │  ◀── rsp
  +──────────────────────────+
low addresses
```

The argument strings sit *below* the environment strings, so each byte you add to the environment pushes the arg strings down by one byte --- and the value of `argv[0]` (the address it points to) shifts by the same amount.

We've turned address-space-layout randomization off for this challenge, so addresses are deterministic: the same launch always produces the same `argv[0]`.

`/challenge/program`:

1. Requires `argc == 1` (no extra arguments).
2. Reads `argv[0]` from the stack.
3. Hands you the flag if `(argv[0] & 0xFFFF) == 0x5390`.

In this challenge, run `/challenge/program` with a clean environment to see where `argv[0]` lands, then tune the length of an environment variable until the low 16 bits of `argv[0]` are `0x5390`:

```text
hacker@dojo:~$ env -i FOO=xxxxxxxx /challenge/program
```

You're not modifying the program at all --- you're just changing **how it's launched**, which controls **where its data ends up**.
