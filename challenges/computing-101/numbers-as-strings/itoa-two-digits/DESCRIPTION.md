One digit was easy.
A two-digit number like `42` needs *splitting* into its tens (`4`) and ones (`2`) --- and splitting is division: `42 / 10 = 4` (the quotient), and `42 % 10 = 2` (the remainder).

x86 gives you *both* results from one `div`, but `div` is a fussy instruction worth learning carefully.
`div rcx` divides the **128-bit** value resulting by concatenating `rdx:rax` by `rcx`, leaving the quotient in `rax` and the remainder in `rdx`.
Two things follow from that:

- It divides `rdx:rax`, not just `rax`, so you must clear `rdx` first (`xor rdx, rdx`) --- otherwise `div` treats leftover garbage as the high half of your number (and may crash).
- The divisor comes from a register, not an immediate, so load the `10` into one (e.g., `mov rcx, 10; div rcx`).
- You don't control the dividend: it's _always_ `rdx:rax`.

After the `div`, `rax` holds the tens and `rdx` holds the ones.
Turn each into a character the way `itoa_digit` did (add `0x30`) and store the two of them.

Write `itoa(value, buf)`, which we'll call from the challenge.
This function should take a value (`10`-`99`) in `rdi` and a pointer to the "output" buffer in `rsi`.
You should parse the number in `rdi` into two characters (using `div` and then your old `itoa_digit` function) and write these two characters to that buffer.
Then return the number of characters written (in this case, 2).
Remember to `.global itoa`.

**Writing characters.**
Your `itoa_digit` function from the last level returned the result (in `rax`), and you didn't have to deal writh writing it to a buffer.
Now, you do.
Your actual character is _one byte_ (8 bits), whereas the register you're holding it in is 64 bits (8 bytes) long.
You just want the last ("least significant") byte, and you can directly access it through _partial register alises_, depending on the register:

| register | least significant byte |
| -------- | ---------------------- |
| `rax`    | `al`                   |
| `rbx`    | `bl`                   |
| `rcx`    | `cl`                   |
| `rdx`    | `dl`                   |
| `rsi`    | `sil`                  |
| `rdi`    | `dil`                  |
| `rbp`    | `bpl`                  |
| `rsp`    | `spl`                  |
| `r8`     | `r8b`                  |
| `r9`     | `r9b`                  |
| `r10`    | `r10b`                 |
| `r11`    | `r11b`                 |
| `r12`    | `r12b`                 |
| `r13`    | `r13b`                 |
| `r14`    | `r14b`                 |
| `r15`    | `r15b`                 |

So, if your character is in `rax`, and the buffer is pointed to by `rsi`, you'll need to do `mov [rsi], al`.

This is tricky, but do it carefully, and the flag is your reward!

----

**Debugging:**
This can get tricky to get right.
To debug this challenge, our advice is to add a `_start` in your code, as so:

```
.global _start
_start:
    mov rdi, 42     // you'll pass 42 as the first argument to your function
    push 0          // this pushes eight 0 bytes to the stack, clearing what will be your output buffer
    mov rsi, rsp    // the output buffer as the second argument to itoa
    int3            // this is optional, if you want gdb to break here without having to set a breakpoint!
    call itoa       // there we go!

    mov rax, 60     // exit cleanly, like a cultured individual
    syscall
```

Assemble and link it as a normal executable (no `-shared` --- this version has an entry point), then load it in `gdb`:

```console
hacker@dojo:~$ as -o debug.o debug.s
hacker@dojo:~$ ld -o debug debug.o
hacker@dojo:~$ gdb ./debug
(gdb) run
```

Execution stops at your `int3`, and from there you can step through with the techniques you learned in [Software Introspection](/computing-101/introspecting), looking at memory on the stack, registers, etc, until things work!
