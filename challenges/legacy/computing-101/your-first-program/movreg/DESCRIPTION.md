Okay, let's learn about one more register: `rsi`!
Like `rdi`, `rsi` is a place you can park some data.
For example:

```assembly
mov rsi, 42
```

Of course, you can also move data around between registers!
Watch:

```assembly
mov rsi, 42
mov rdi, rsi
```

Just like the first line there moves `42` into `rsi`, the second line moves the value in `rsi` to `rdi`.
Here, we have to mention one complication: by _move_, we really mean _set_.
After the snippet above, `rsi` _and_ `rdi` will be `42`.
It's a mystery as to why the `mov` was chosen rather than something reasonable like `set` (even very knowledgeable people resort to [wild speculation](https://retrocomputing.stackexchange.com/questions/12968/why-is-the-processor-instruction-called-move-not-copy) when asked), but it was, and here we are.

Anyways, on to the challenge!
In this challenge, we will store a secret value in the `rsi` register, and your program must exit with that value as the return code.
Since `exit` uses the value stored in `rdi` as the return code, you'll need to move the secret value in `rsi` into `rdi`.
Run `/challenge/check` and pass it your code for the flag! `/challenge/check` will set the secret value in `rsi` before running your code.
Good luck!
