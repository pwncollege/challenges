Now, let's teach the calculator to multiply!

Multiplication has its own instruction: `imul`.
Just as you used `add` for `'+'` and `sub` for `'-'`, you'll use `imul` for `'*'`.
You've already met it back in `atoi-two-digits`, where `imul rax, 10` scaled your running total by ten; here it multiplies your two operands the same way.

```
"6"   ->  atoi  ->   6
"7"   ->  atoi  ->   7
6  *  7  =  42
42   ->  itoa  ->  "42"
```

Add a third branch on the operator byte: if it's `'*'`, `imul` the operands; `'+'` and `'-'` work as before, and any other operator still makes you quit with a nonzero exit code.

One shell wrinkle: `*` is special to the shell (it expands to filenames), so quote it when you run your program by hand --- `./prog 6 '*' 7` or `./prog 6 "*" 7`.
The character your program receives is still a plain `'*'`.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 6 '*' 7
42
hacker@dojo:~$ /challenge/check prog
```

Add the multiply branch and print the product.
