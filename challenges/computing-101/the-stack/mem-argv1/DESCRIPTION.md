You've now read `[rsp]` to get the argument count, and `[rsp+128]` to get data at an offset.
Let's look at what else is on the stack!

Right after the argument count, the stack stores _pointers_ to each program argument.
These are _addresses_ stored in memory: `[rsp+16]` doesn't contain the argument text directly --- it contains the _address_ where that text lives.

For example, if your program is run as `/tmp/your-program Hi`:

```text
     Register │ Contents
   +───────────────────────────+
   │ rsp      │ 1337000        │─┐
   +───────────────────────────+ │
                                 │
  ┌──────────────────────────────┘
  │
  │    Address    │ Contents
  │  +────────────────────────+
  │  │ ...        │ ...       │
  │  +────────────────────────+
  └▸ │ 1337000    │ 2         │  ◀── the ARGument Count (termed "argc")
     +────────────────────────+
     │ 1337008    │ 1234000   │──────┐
     +────────────────────────+      │
     │ 1337016    │ 1234560   │────┐ │
     +────────────────────────+    │ │
     │ 1337024    │ 0         │    │ │
     +────────────────────────+    │ │
                                   │ │
   ┌───────────────────────────────┘ │
   │                                 │
   │   Address   │ Contents          │
   │ +──────────────────────────+    │
   │ │ 1234000   │ "/tmp/..."   │◀───┘
   │ +──────────────────────────+
   │ │ ...       │ ...          │
   │ +──────────────────────────+
   └▸│ 1234560   │ "Hi"         │
     +──────────────────────────+
```

To get the actual argument data, you need to dereference twice: once to get the pointer from the stack, and once to follow it to the data.

```assembly
mov rdi, [rsp+16]   # load the argv[1] pointer (e.g., 1234000) from the stack
mov rdi, [rdi]      # follow the pointer to read the actual data (e.g., "Hi")
```

In this challenge, your program will be invoked with an argument.
Read the value of `argv[1]` and exit with it!
