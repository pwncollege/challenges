So far you've been on the *callee* side of a function call: the grader called your `solve`, and you did the work.
Now we flip it: your `solve` will receive a function pointer as an argument, and **you have to call that function** from your code.

A function pointer is just an address: a 64-bit value that names the location of some code in memory.
To call a function whose address sits in a register, x86-64 gives you a register form of the `call` instruction:

```text
call rdi
```

This does exactly what `call <label>` does, except the target is taken from a register instead of a literal:

1. Push the address of the next instruction onto the stack (the return address).
2. Jump to the address held in `rdi`.

When the callee eventually executes `ret`, it pops that return address and you continue from right after your `call`.

For this challenge:

- `rdi` will contain a function pointer.
- Your job: call the function in `rdi`, then `ret` to return control to the grader.

The grader will verify that the function in `rdi` got called.

As before, build a shared library and pass it to the grader:

```sh
as --64 your-solve.s -o your-solve.o
ld -shared your-solve.o -o your-solve.so
/challenge/check your-solve.so
```
