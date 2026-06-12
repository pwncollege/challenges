In the previous level, you read `envp[0]` --- a pointer that the kernel placed on the stack, pointing _into_ the strings region above the pointer tables.
The same layout applies here:

```text
     Address    │ Contents
   +────────────────────────+
   │ rsp + 0    │ 1         │ ◀─── argc
   +────────────────────────+
   │ rsp + 8    │ rsp + 128 │───────┐  argv[0]: pointer to the program name
   +────────────────────────+       │
   │ rsp + 16   │ 0         │       │  NULL (end of argv)
   +────────────────────────+       │
   │ rsp + 24   │ rsp + 200 │─────┐ │  envp[0]: pointer to the first env var
   +────────────────────────+     │ │
   │ rsp + 32   │ 0         │     │ │  NULL (end of envp)
   +────────────────────────+     │ │
                                  │ │
  ┌───────────────────────────────│─┘
  │                               │
  │   Address   │ Contents        │
  │ +──────────────────────────+  │
  │ │ rsp + 128 │ "/tmp/..."   │◀─┘ the program name
  │ +──────────────────────────+
  │ │ ...       │ ...          │
  │ +──────────────────────────+
  └▸│ rsp + 200 │ "FOO=..."    │ ◀─ the first env var
    +──────────────────────────+
```

But where do the actual addresses (`rsp`, or the actual address that `rsp+200` resolves to, etc.) come from?

When your program is launched, the kernel **fills the stack backwards** from some chosen starting address.
From there, it lays down the env strings ("growing" toward smaller addresses), then the arg strings, other metadata, then the `envp[]` and `argv[]` pointer tables, and finally `argc` on the leftmost side of the structure.
That's where `rsp` ends up pointing.

This has an interesting consequence: **the more bytes you stuff into the environment (or the program arguments), the further "left" the stack the kernel pushes everything else**.
An extra env byte means `rsp` ends up at a smaller address, the arg-strings region sits one byte further "left", and `argv[0]` (a pointer into that region) holds a one-byte-smaller value.

Here, `env -i` means "run the following command with an empty environment"; any `NAME=VALUE` pairs you put after `-i` are the only environment strings the child program receives.
In this challenge, take a clean baseline with `env -i /challenge/program` to see what address it wants `argv[0]` at.
Then run it again with exactly one environment variable, with just the right number of `x`s in its value, to shift `argv[0]` to that address.
Use `env -i` for both runs so your shell's own variables do not also land on the stack and throw off your count:

```text
hacker@dojo:~$ env -i /challenge/program
hacker@dojo:~$ env -i FOO=xxxxxxxx /challenge/program
```

Remember that the whole environment string is placed on the stack, so `FOO=` and the trailing null byte count toward the shift too.
You're not modifying the program at all, just changing how it's launched, which influences where its data ends up!
