In the previous challenge, you wrote assembly that compared strings character by character.
Well, the tables have turned!
_We_ wrote a program, and _you_ need to figure out what it does!

At `/challenge/reverse-me`, there's a SUID binary.
It takes a command-line argument, compares it against a hidden password one byte at a time (sound familiar?) and, if the password is correct, reads and prints the flag.
If any character is wrong, it silently exits.

How do you solve this?
You must read the disassembly of the program, analyze the `cmp` instructions, understand the password that the program needs, then run it with the correct argument.

You already have the tools for this!
From the [Software Introspection](/computing-101/software-introspection) module, remember: `objdump -d -M intel /challenge/reverse-me` disassembles the binary and shows its assembly instructions.
You'll see familiar `cmp` instructions similar to those you wrote in the last challenge, but instead of the familiar `''`-quoted characters, the compared-against values will be written as hex.
The immediate values in those comparisons _are_ the password characters, encoded as hexadecimal ASCII values.

For example, imagine that the disassembly shows:

```
cmp    BYTE PTR [rax],0x70
```

Here, `0x70` is the ASCII code for `'p'`.
You can get the full list of ASCII values by referencing the `man ascii` command.

Once you've recovered all the password characters, run the program directly:

```console
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary --- it runs with elevated privileges so it can read `/flag`.
However, **debugging a program will drop its SUID privileges**, which means the `open("/flag")` syscall inside will **silently** fail if you run it under gdb.
You can use gdb or `objdump` to _understand_ the binary and figure out the password, but make sure to run it **directly** (outside of gdb) to get the flag.
