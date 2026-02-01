You've now read `[rsp]` to get the argument count, and `[rsp+128]` to get data at an offset.
Let's look at what else is on the stack!

Right after the argument count, the stack stores _pointers_ to each argument string:

```text
    Address    | Contents
  +------------------------------------------+
  | rsp        | argc (argument count)       |
  +------------------------------------------+
  | rsp+8      | argv[0] (pointer to name)   |
  +------------------------------------------+
  | rsp+16     | argv[1] (pointer to arg 1)  |
  +------------------------------------------+
  | rsp+24     | argv[2] (pointer to arg 2)  |
  +------------------------------------------+
  | ...        | ...                         |
  +------------------------------------------+
```

These are _addresses_ stored in memory.
`[rsp+16]` doesn't contain the argument text directly --- it contains the _address_ where that text lives.
To get the actual data, you need to dereference twice: once to get the pointer from the stack, and once to follow it to the data.

For example:

```assembly
mov rdi, [rsp+16]   # load the argv[1] pointer from the stack
mov rdi, [rdi]       # follow the pointer to read the actual data
```

In this challenge, your program will be invoked with an argument.
Read the value of `argv[1]` and exit with it!
