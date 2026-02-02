In the previous challenge, you reversed a program by finding password characters directly in the `cmp` instructions.
This time, the program _transforms_ your input before comparing it.
You'll need to understand and mentally invert this operation to successfully pass the check!

At `/challenge/reverse-me`, there's a new SUID binary.
It will do some math on the first byte of the first program argument, and compare it against a hardcoded value.
If the comparison passes, it reads and prints the flag.
Otherwise, it silently exits.

The new instruction here is `add`, as so:

```asm
add rax, 42
```

This adds 42 to the `rax` register and updates `rax` with the result.
The following would result in `rax` having the value 99:

```asm
mov rax, 57
add rax, 42
```

Like many other instructions, `add` can handle memory, registers, or immediates, when you disassemble this binary with `objdump -d -M intel /challenge/reverse-me`, you might see something like:

```
add    BYTE PTR [rax],0x2a
cmp    BYTE PTR [rax],0x96
```

This adds `0x2a` (42) to the first byte of your input (in memory), then checks if the result equals `0x96` (150).
To figure out what character you need, just reverse the math: `150 - 42 = 108` (`6c`).
Looking at `man ascii`, `0x6c` is the character `'l'`.
So the required input character in this case is `l` (remember, `man ascii` is your friend for converting between hex values and characters)!

Once you've figured out the character, run the program:

```console
hacker@dojo:~$ /challenge/reverse-me YOUR_CHARACTER_HERE
```

Now it's your turn!
Go and get the flag.

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary --- it runs with elevated privileges so it can read `/flag`.
However, **debugging a program will drop its SUID privileges**, which means the `open("/flag")` syscall inside will **silently** fail if you run it under gdb.
You can use gdb or `objdump` to _understand_ the binary, but make sure to run it **directly** (outside of gdb) to get the flag.
