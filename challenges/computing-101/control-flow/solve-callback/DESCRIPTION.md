So far you've been on the _callee_ side of a function call: the challenge called your `solve`, and you did the work.
Now we flip it: your `solve` will receive a function pointer as an argument, and **you have to call that function** from your code.

A function pointer is just an address: a 64-bit value that names the location of some code in memory.
The challenge passes the pointer in `rdi` (the first argument to your function), so to call it you can use the register form of `call`:

```text
call rdi
```

This pushes the address of the instruction after the `call` (the _return address_) onto the stack, then jumps to the address held in `rdi`.
When that callback eventually `ret`s, your function's execution will continue right after your `call rdi` --- the same `call`/`ret` pair you learned in the previous two levels.

The callback prints the flag for you. Go for it!
