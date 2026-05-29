So far you've been on the _callee_ side of a function call: the challenge called your `solve`, and you did the work.
Now we flip it: your `solve` will receive a function pointer as an argument, and **you have to call that function** from your code.

A function pointer is just an address: a 64-bit value that names the location of some code in memory.
To call a function whose address sits in a register, x86-64 gives you a register form of the `call` instruction:

```text
call rdi
```

This does exactly what `call <label>` does, except the target is taken from a register instead of a literal:

1. Pushes the address of the instruction after the `call` (the _return address_) onto the stack.
2. Jumps to the address held in `rdi`.

When _that_ callee eventually executes `ret`, it pops the return address and execution continues from right after your `call rdi`, exactly the same `call`/`ret` pair you learned about in the previous two challenges.

For this challenge:

- `rdi` will contain a pointer pointing to a function that will print the flag.
- You have to call the function in `rdi`, then `ret` to return control back to the challenge.

That's it!
The challenge will verify that the function in `rdi` actually got called, and once it does, it will give you the flag!
