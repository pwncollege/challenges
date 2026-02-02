Okay, let's stretch that to one more depth!
We've added an additional level of indirection in this challenge, so now you'll need *three* dereferences to find the secret value.
Something like this:

```text
        Address │ Contents
      +────────────────────+
┌────▸│ 133700  │ 123400   │───┐
│     +────────────────────+   │
│ ┌──▸│ 123400  │ 100000   │─┐ │
│ │   +────────────────────+ │ │
│ │ ┌▸│ 100000  │ 42       │ │ │
│ │ │ +────────────────────+ │ │
│ │ └────────────────────────┘ │
│ └────────────────────────────┘
└──────────────────────────────┐
                               │
       Register │ Contents     │
      +────────────────────+   │
      │ rdi     │ 133700   │───┘
      +────────────────────+
```

As you can see, we'll place the first address that you must dereference into rdi.
Go get the value!
