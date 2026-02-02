In the last level, you used `x` to read `argc` from the top of the stack.
But the stack holds more than just `argc`!

Right after the argument count, the stack stores _pointers_ to each program argument.
These are _addresses_ stored in memory: `$rsp+16` doesn't contain the argument text directly --- it contains the _address_ where that text lives.

For example, if your program is run as `/challenge/debug-me Hi`:

```text
     Address    │ Contents
   +────────────────────────────+
   │  rsp + 0   │ 2             │◀── argc
   +────────────────────────────+
   │  rsp + 8   │ 0x1234000     │──────┐
   +────────────────────────────+      │
   │  rsp + 16  │ 0x1234560     │────┐ │
   +────────────────────────────+    │ │
                                     │ │
                                     │ │
     Address    │ Contents           │ │
   +──────────────────────────────+  │ │
   │ 0x1234000  │ "/challenge/..."│◀─│─┘ the program name
   +──────────────────────────────+  │
   │ ...        │ ...                │
   +──────────────────────────────+  │
   │ 0x1234560  │ "Hi"            │◀─┘   the first argument
   +──────────────────────────────+
```

To get the actual argument data, you need two dereferences: one to get the pointer from the stack, and one to follow it to the string.

In this level, THE FLAG ITSELF is passed as the first argument!
The program doesn't use it --- it just exits --- but the flag is right there in memory.

To find it, you'll need two `x` commands, with two different display modes:

**First:**
You'll need the _pointer_ the first argument.
You've done this before, but now you're doing it in gdb.

```text
x/a $rsp+16
```

`/a` tells `x` to display the value as a memory **a**ddress.
You'll see a very large hexadecimal number, something like `0x7ffc001c4750`.

**Second:**
Read the text of the first argument at that address:

```text
x/s 0x7ffc001c4750
```

`/s` tells `x` to display the value as a **s**tring.
Replace the address with whatever you got from step 1.
This will show you the flag!

Go and do that!

1. Start the program
2. `x/a $rsp+16` to get the address of the first argument
3. `x/s <address>` to read the flag string
