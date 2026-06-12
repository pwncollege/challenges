Your two-digit `atoi` did `first * 10 + second`.
What if there are more than two digits?
Of course, you'd keep a running total, and for each new digit do `total = total * 10 + digit`.
That repetition is a _loop_, which you've read before, but will write here!

Read the digits left to right:

```
"123":
  total = 0
  '1':  total =  0*10 + 1  =   1
  '2':  total =  1*10 + 2  =  12
  '3':  total = 12*10 + 3  = 123
```

You would do this until the end of the string, which, by the convention of the C programming language (and used here), is represented by a byte with a value of 0x00 (that is, binary `00000000` or decimal _value_ 0).
Note that this is distinct from the character '0', which, again, has a value of `0x30` (binary `00110000`).

So, your loop is: look at the next byte, if it's `0`, jump beyond the loop (look back at the [Looping](https://pwn.college/computing-101/control-flow/loop) challenge for reference), otherwise multiply the total by `10`, call `atoi_digit` to convert the digit, and add it to the total, then loop back to the head of the loop.
Easy!

Your `atoi` receives a pointer to the string in `rdi` and must return the integer value in `rax`.
Loop the digits and return the number.

----

**Debugging:**
This can get tricky to get right.
To debug this challenge, our advice is to add a `_start` to your code that fakes the call, as so:

```
.global _start
_start:
    push 0x333231   // "123" on the stack -- little-endian, so 0x31 ('1') is the first byte, and the high zero bytes terminate it
    mov rdi, rsp    // a pointer to that string, as the first argument to atoi
    int3            // this is optional, if you want gdb to break here without having to set a breakpoint!
    call atoi       // there we go!

    mov rdi, rax    // atoi's result comes back in rax; exit with it so you can read it back with `echo $?`
    mov rax, 60     // exit
    syscall
```

Assemble and link it as a normal executable (no `-shared` --- this version has an entry point), then load it in `gdb`:

```console
hacker@dojo:~$ as -o debug.o debug.s
hacker@dojo:~$ ld -o debug debug.o
hacker@dojo:~$ gdb ./debug
(gdb) run
```

Execution stops at your `int3`, and from there you can step through with the techniques you learned in [Software Introspection](/computing-101/introspecting), watching `rdi` walk the string and your running total build up in `rax`, until things work!
