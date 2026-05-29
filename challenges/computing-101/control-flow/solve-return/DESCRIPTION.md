In the previous challenge, your `solve` function ended with an `exit` syscall.
That worked, but it also meant the caller never got control back --- once you exited, the whole process was gone.
In a real program, of course, this is not ideal.

A real callee is supposed to _hand control back_ to whoever called it, so the caller can continue doing its own work.
That's what the **`ret`** (return) instruction is for.

Recall the `call` instruction from the previous challenge: it pushed a _return address_ onto the stack before jumping into your code.
`ret` is the matching half: it **pops that saved return address off the stack and jumps to it**.
Together, `call` and `ret` form the basic function-call/function-return pair in x86 --- one to get into a function, one to get back out.

In this challenge, your `solve` function has to **return a value** back to the challenge.
In the Linux x86-64 calling convention, **the return value of a function goes in `rax`**.
You've already seen `rax` used in syscalls --- it holds the syscall number on entry and the syscall's result on exit.
The same register also holds the return value of a regular function.

The mechanics:

1. The challenge executes `call solve`, passing one argument in `rdi`.
2. Your function does some work.
3. Your function puts its result in `rax`.
4. Your function executes `ret`, which pops the saved return address off the stack and jumps back to the challenge.
5. The challenge reads `rax` and treats it as your function's return value.

For this challenge:

- `rdi` will contain a secret 64-bit value chosen at random by the grader.
- Your function must return `rdi + 1` in `rax`.

That's it!
Once the challenge receives the correct value, it will give you the flag!
