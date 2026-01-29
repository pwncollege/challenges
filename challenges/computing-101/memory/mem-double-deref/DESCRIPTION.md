In the last few levels, you have:

- Used an address that we told you (in one level, `133700`, and in another, `123400`) to load a secret value from memory.
- Used an address that we put into `rax` for you to load a secret value from memory.
- Used an address that we told you (in the last level, `567800`) to load _the address_ of a secret value from memory into a register, then used that register as a pointer to retrieve the secret value from memory!

Let's put those last two together.
In this challenge, we stored our `SECRET_VALUE` in memory at the address `SECRET_LOCATION_1`, then stored `SECRET_LOCATION_1` in memory at the address `SECRET_LOCATION_2`.
Then, we put `SECRET_LOCATION_2` into `rax`!
The result looks something like this, using `123400` for `SECRET_LOCATION_1` and `133700` for `SECRET_LOCATION_2` (not, in the real challenge, these values will be different and hidden from you!):

```text
      Address │ Contents
    +────────────────────+
┌──▸│ 133700  │ 123400   │─┐
│   +────────────────────+ │
│ ┌▸│ 123400  │ 42       │ │
│ │ +────────────────────+ │
│ └────────────────────────┘
└──────────────────────────┐
                           │
     Register │ Contents   │
    +────────────────────+ │
    │ rax     │ 133700   │─┘
    +────────────────────+
```

Here, you will need to perform two memory reads: one dereferencing `rax` to read `SECRET_LOCATION_1` from the location that `rax` is pointing to (which is `SECRET_LOCATION_2`), and the second one dereferencing whatever register now holds `SECRET_LOCATION_1` to read `SECRET_VALUE` into `rdi`, so you can use it as the exit code!

That sounds like a lot, but you've done basically all of this already.
Go put it together!
