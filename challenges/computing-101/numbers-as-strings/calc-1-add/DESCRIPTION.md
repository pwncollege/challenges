You can read a number from text with your `atoi`, and write one back to text with your `itoa`.
Now you'll put both to work in a single program: a calculator.

A calculator reads an expression like `6 + 7` and prints the answer.
We'll hand you that expression three pieces at a time, on the command line:

```
prog 6 + 7
```

So `argv[1]` is the left operand (`"6"`), `argv[2]` is the operator (`"+"`), and `argv[3]` is the right operand (`"7"`).
Each one is a string, just like the arguments you've already been reading off the stack.
Recall that `argc` sits at `[rsp]`, and the argument pointers follow: `argv[0]` at `[rsp + 8]`, `argv[1]` at `[rsp + 16]`, `argv[2]` at `[rsp + 24]`, and `argv[3]` at `[rsp + 32]`.

The operand strings are easy: `atoi` each one to get its value, exactly as before.
The operator is the new piece.
It's a string too, but a one-character one, so the character you care about is its first byte: `argv[2][0]`.
Load that pointer and read the byte it points at, and you have the operator as a single character to branch on.

For this level there's only one operator to handle, `'+'`:

```
"6"   ->  atoi  ->   6
"7"   ->  atoi  ->   7
6  +  7  =  13
13   ->  itoa  ->  "13"
```

But a real operator might be anything the user typed, and you only know how to add.
So check the operator byte first: if it's `'+'`, do the addition; if it's anything else, you don't support it, so quit by exiting with a nonzero code (no answer to print).
That refusal is part of the job --- recognizing the one operator you handle, and bailing out on the rest.

When the operator is `'+'`: `atoi` both operands, add them, `itoa` the sum into a scratch buffer, and `write` those bytes to file descriptor `1` (standard output).
Reserve that buffer on the stack (a `sub rsp, 0x80` makes room, and `rsp` then points at it), the same way you stored the `/flag` string on the stack back in [Hello, Hackers](/computing-101/hello-hackers).
Then exit cleanly with code `0`.

This is a whole program, so assemble and link it as one (no `-shared`), then submit it:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 6 + 7
13
hacker@dojo:~$ /challenge/check prog
```

Read the operands, dispatch on the operator, and print the sum.
