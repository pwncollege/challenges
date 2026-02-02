So far, your programs have been fairly straightforward: move some values around, read from memory, and invoke a system call.
But real programs need to make _decisions_: "if this condition is true, do one thing; otherwise, do something else."
This is the foundation of **control flow**, and it starts with being able to _compare_ values.

In x86 assembly, comparisons are done with the `cmp` instruction.
`cmp` compares two values by subtracting the second operand from the first.
Crucially, **`cmp` doesn't store the result of the subtraction** anywhere you can see directly.
Instead, it updates the CPU's internal **flags** based on what the result looked like.

For example:

```asm
cmp rdi, 42
```

This internally computes `rdi - 42`, but `rdi` is _not_ modified.
Instead, the CPU sets a special bit called the **Zero Flag** (ZF): if the result of the subtraction was zero (meaning the two values were equal), ZF is set to 1.
If `rdi` contains `42`, then `42 - 42 = 0`, and ZF becomes 1.
If `rdi` contains anything else, the result is non-zero, and ZF becomes 0.

Great, so after `cmp`, the CPU knows whether the values were equal.
But how do we actually _use_ that information?

We can't directly `mov` the flags into a register.
Instead, x86 provides a family of "set on condition" instructions that write a `0` or `1` to a byte-sized destination based on the current flags.

The one we'll use here is `setz` ("Set if Zero"):

```asm
setz dil
```

This checks the Zero Flag and:
- If ZF = 1 (the values **were** equal, i.e., the subtraction result was zero), it writes `1` to `dil`.
- If ZF = 0 (the values were **not** equal), it writes `0` to `dil`.

Simple: `1` means "yes, they matched!" and `0` means "no, they didn't."
There's also a complementary instruction, `setnz` ("Set if Not Zero"), which does the opposite, but we won't need it here.

But what is `dil`?
So far, you've worked with 64-bit registers like `rdi`, `rax`, and `rsp`.
The `setnz` instruction, however, only writes a single byte (8 bits).
Luckily, you can access smaller portions of the full 64-bit registers.
For `rdi`:

- `rdi` is the full 64 bits
- `dil` is just the lowest 8 bits --- the **l**ow byte of r**di**

When you write `setz dil`, you're putting a `0` or `1` into just the lowest byte of `rdi`, leaving the upper bytes unchanged.
Since `rdi` is the register used for the exit code in the `exit` system call, this effectively makes your exit code `1` (equal!) or `0` (not equal!).

One more thing about `cmp`: it can compare a register with an immediate (`cmp rdi, 42`) or even a memory location with an immediate (`cmp BYTE PTR [rsp], 42`).
But it **cannot** compare two memory locations at once --- at most one operand can be a memory dereference.
This is a general rule in x86 and, actually, in almost all CPU architectures.

Now, your challenge: recall from the [Stack](/computing-101/the-stack) module that `[rsp]` contains `argc` --- the number of command-line arguments passed to your program, including the program name.
Write a program that:

1. Compares `argc` with `42` (whether by first moving argc into a register or comparing against the memory directly).
2. Uses `setz dil` to set the exit code: `1` if argc equals 42, `0` otherwise.
3. Exits.
