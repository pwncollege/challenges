Did you prefer to access memory at `133700` or at `123400`?
Your answer might say something about your personality, but it's not super relevant from a technical perspective.
In fact, in most cases, you don't deal with actual memory addresses when writing programs at all!

How is this possible?
Well, typically, memory addresses are stored in registers, and we use the values in the registers to point to data in memory!
Let's start with this memory configuration:

```text
  Address │ Contents
+────────────────────+
│ 133700  │ 42       │
+────────────────────+
```

And consider this assembly snippet:

```assembly
mov rax, 133700
```

Now, what you have is the following situation:

```text
    Address │ Contents
  +────────────────────+
┌▸│ 133700  │ 42       │
│ +────────────────────+
│
└────────────────────────┐
                         │
   Register │ Contents   │
  +────────────────────+ │
  │ rax     │ 133700   │─┘
  +────────────────────+
```

`rax` now holds a value that corresponds with the address of the data that we want to load!
Let's load it:

```assembly
mov rdi, [rax]
```

Here, we are accessing memory, but instead of specifying a fixed address like `133700` for the memory read, we're using the value stored in `rax` as the memory address.
By containing the memory address, `rax` is a _pointer_ that _points to_ the data we want to access!
When we use `rax` in lieu of directly specifying the address that it stores to access the memory address that it references, we call this _dereferencing_ the pointer.
In the above example, we _dereference_ `rax` to load the data it points to (the value `42` at address `133700`) into `rdi`.
Neat!

This also drives home another point: these registers are _general purpose_!
Just because we've been using `rax` as the syscall index in our challenges so far doesn't mean that it can't have other uses as well.
Here, it's used as a pointer to our secret data in memory.

Similarly, the _data_ in the registers doesn't have an implicit purpose.
If `rax` contains the value `133700` and we write `mov rdi, [rax]`, the CPU uses the value as a memory address to dereference.
But if we write `mov rdi, rax` in the same conditions, the CPU just happily puts `133700` into `rdi`.
To the CPU, data is data; it only becomes differentiated when it's used in different ways.

In this challenge, we've initialized `rax` to contain the address of the secret data we've stored in memory.
Dereference `rax` to load the secret data into `rdi` and use it as the exit code of the program to get the flag!
