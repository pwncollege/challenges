In the previous challenge, you read the value at `[rsp]`: the very top of the stack.
But the stack has lots of data on it, and you can access any of it by adding an _offset_ to `rsp`.

For example, `[rsp+8]` reads the 8-byte value right _after_ `[rsp]`, `[rsp+16]` reads the next one after that, and so on.
In general, `[rsp+N]` reads memory at the address `rsp+N`:

```text
    Address    | Contents
  +---------------------------+
  | rsp        | value 0      |  <-- [rsp]
  +---------------------------+
  | rsp+8      | value 1      |  <-- [rsp+8]
  +---------------------------+
  | rsp+16     | value 2      |  <-- [rsp+16]
  +---------------------------+
  | ...        | ...          |
  +---------------------------+
```

You'll notice these offsets go in multiples of 8.
That's because many values on the stack, such as numbers or memory addresses, tend to be 8 bytes (64 bits) wide, so consecutive values are 8 bytes apart.
But this is mostly convention: in reality, the stack, like any other region of memory, is a contiguous region of individual bytes, though for now we'll treat the stack as a bunch of 8-byte/64-bit values.

In this challenge, we've stashed a secret value on the stack at an offset of 128 bytes from `rsp`.
Read the value at `[rsp+128]` and use it as the exit code!
