In the previous level, the filename was passed as an argument to your program.
But what if you need to open a file whose path you already know?
You can hardcode the filename string directly into your program by writing it onto the stack, byte by byte!

The `open` syscall needs a _pointer_ to the filename, so you need the bytes `/ f l a g` stored somewhere in memory.
You already know a writable memory address: `rsp` (the stack).
You can write each character one byte at a time:

```asm
mov BYTE PTR [rsp], '/'
mov BYTE PTR [rsp+1], 'f'
mov BYTE PTR [rsp+2], 'l'
mov BYTE PTR [rsp+3], 'a'
mov BYTE PTR [rsp+4], 'g'
mov BYTE PTR [rsp+5], 0
```

A few things to note here:

- **`BYTE PTR`**: When you write to a memory address like `[rsp]` using an _immediate value_ (a number or character), the CPU doesn't know how many bytes you intend to write --- one? two? eight? `BYTE PTR` is a _size directive_ that tells the assembler "I mean exactly one byte." Without it, the assembler won't know what you want and will refuse to assemble the instruction.

- **Single quotes**: In assembly, a single-quoted character like `'f'` represents that character's one-byte ASCII value. So `'f'` is just a convenient way of writing `0x66`, and `'/'` is `0x2f`.

- **The null byte**: The last byte we write is `0` --- a special _null_ byte. This is how Linux knows where a string ends: it reads bytes starting from the pointer you give it and stops when it hits a `0` byte. Without it, `open` would keep reading past `"flag"` into whatever else is on the stack, and you'd be trying to open a file with a nonsense name!

After writing these bytes, `rsp` points to the null-terminated string `"/flag"`, ready to pass to `open`.

**Your turn!**
This time, no arguments are passed to your program.
You must construct the filename yourself.

Your program should:

1. Write `"/flag\0"` onto the stack byte by byte using `mov BYTE PTR [rsp+N], ...`
2. `open` it (syscall `2`): `rdi` = `rsp` (the string you just wrote), `rsi` = `0`
3. `read` 64 bytes from the returned fd into memory (syscall `0`)
4. `write` those 64 bytes to stdout (syscall `1`)
5. `exit` with code `42` (syscall `60`)

----
**DEBUGGING:**
Having trouble?
Use `strace` to trace your syscalls.
If `open` returns `-1`, your string pointer or encoding might be off.
Try `x/s $rsp` in `gdb` to see what string is actually on the stack.
