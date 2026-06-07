Back in `nums-first`, your program could only report its answer as an *exit code* --- one byte, `0` to `255`.
To hand back a real number, a program has to *print* it, and that means turning the number into text first.
That's `itoa` (integer to ASCII): the mirror of `atoi`, and we'll build it the same way, one digit at a time.

A digit's character is just its value plus `'0'`.
That's the reverse of `atoi_digit`, which went from `'7'` to `7` by *subtracting* `'0'`; here you *add* it:

```
7  ->  7 + 0x30  =  0x37  =  '7'
```

Your `itoa_digit` gets a value in `rdi` (a single digit, `0`-`9`) and returns its ASCII character in `rax`.
Remember to `.global itoa_digit` so the challenge can find it.

Build and submit as before:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Add `'0'`, return the character, and score!
