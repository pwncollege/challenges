So now you can dereference pointers in memory like a pro!
But pointers don't always point directly at the data you need.
Sometimes, for example, a pointer might point to a collection of data (say, an entire book), and you'll need to reference partway into this collection for the specific data you need.

For example, if your pointer (say, `rdi`) points to a sequence of numbers in memory, as so:

```text
    Address │ Contents
  +────────────────────+
┌▸│ 133700  │ 50       │
│ │ 133701  │ 42       │
│ │ 133702  │ 99       │
│ │ 133703  │ 14       │
│ +────────────────────+
│
└────────────────────────┐
                         │
   Register │ Contents   │
  +────────────────────+ │
  │ rdi     │ 133700   │─┘
  +────────────────────+
```


If you want the second number of that sequence, you could do:

```assembly
mov rax, [rdi+1]
```

Wow, super simple!
In memory terms, we call these number slots _bytes_: each memory address represents a specific byte of memory.
The above example is accessing memory 1 byte after the memory address pointed to by `rdi`.
In memory terms, we call this 1 byte difference an _offset_, so in this example, there is an offset of 1 from the address pointed to by `rdi`.

Let's practice this concept.
As before, we will initialize `rdi` to point at the secret value, but not _directly_ at it.
This time, the secret value will have an offset of 8 bytes from where `rdi` points, something analogous to this:

```text
    Address │ Contents
  +────────────────────+
┌▸│ 31337   │ 0        │
│ │ 31337+1 │ 0        │
│ │ 31337+2 │ 0        │
│ │ 31337+3 │ 0        │
│ │ 31337+4 │ 0        │
│ │ 31337+5 │ 0        │
│ │ 31337+6 │ 0        │
│ │ 31337+7 │ 0        │
│ │ 31337+8 │ ???      │
│ +────────────────────+
│
└────────────────────────┐
                         │
   Register │ Contents   │
  +────────────────────+ │
  │ rdi     │ 31337    │─┘
  +────────────────────+
```

Of course, the actual memory address is not `31337`.
We'll choose it randomly, and store it in `rdi`.
Go dereference `rdi` with offset `8` and get the flag!
