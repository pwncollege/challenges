Now any length.
A number of any size is that same `div`-by-10 step, repeated: each `div` peels off the lowest digit (the remainder) and shrinks the number (the quotient), until the number reaches `0`.

```
123:  123 % 10 = 3,  123 / 10 = 12
       12 % 10 = 2,   12 / 10 = 1
        1 % 10 = 1,    1 / 10 = 0   (stop)
```

But notice the catch: the digits come out **backwards** --- ones first (`3`, `2`, `1`), the reverse of how you write them (`1`, `2`, `3`).
So you can't just append them as you go.
The usual fixes: stash each digit as it comes and write them out in reverse (the stack is perfect for this --- `push` them as they fall out, `pop` them to write, and LIFO reverses them for free), or write them into the buffer from the back toward the front.

One edge case to watch: `0` itself.
The loop above runs zero times for it (it's already `0`), so you'd write nothing --- handle it as a plain `"0"`.

Write `itoa(value, buf)` for any non-negative `value` (in `rdi`, buffer in `rsi`): write its decimal digits to the buffer and return how many you wrote, in `rax`.
Remember to `.global itoa`.

Build and submit as before:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Reverse the digits, return the length, and score!
