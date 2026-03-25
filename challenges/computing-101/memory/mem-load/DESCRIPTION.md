As seen by your program, computer memory is a huge place where data is housed.
Like houses on a street, every part of memory has a numeric _address_, and like houses on a street, these numbers are (mostly) sequential.
Modern computers have enormous amounts of memory, and the view of memory of a typical modern program actually has large gaps (think: a portion of the street that hasn't had houses built on it, and so those addresses are skipped).
But these are all details: the point is, computers store data, mostly sequentially, in memory.

In this level, we will practice accessing data stored in memory.
How might we do this?
Recall that to move a value into a register, we did something like:

```assembly
mov rdi, 31337
```

After this, the value of `rdi` is `31337`.
Cool.
Well, we can use the same instruction to access memory!
There is another format of the command that, instead, uses the second parameter as an address to access memory!
Consider that our memory looks like this:

```text
  Address │ Contents
+────────────────────+
│ 31337   │ 42       │
+────────────────────+
```

To access the memory contents at memory address 31337, you can do:

```assembly
mov rdi, [31337]
```

When the CPU executes this instruction, it of course understands that `31337` is an _address_, not a raw value.
If you think of the instruction as a person telling the CPU what to do, and we stick with our "houses on a street" analogy, then instead of just handing the CPU data, the instruction/person _points at a house on the street_.
The CPU will then go to that address, ring its doorbell, open its front door, drag the data that's in there out, and put it into `rdi`.
Thus, the `31337` in this context is the _memory address_ and serves to _point to_ the data stored at that memory address.
After this instruction executes, the value stored in `rdi` will be `42`!

Let's put this into practice!
I've stored a secret number at memory address `133700`, as so:

```text
  Address │ Contents
+────────────────────+
│ 133700  │ ???      │
+────────────────────+
```

You must retrieve this secret number and use it as the exit code for your program.
To do this, you must read it into `rdi`, whose value, if you recall, is the first parameter to `exit` and is used as the exit code.
Good luck!
