In the previous level, you called the callback with `call rdi` --- easy, since the pointer was already in `rdi`.
This time, you have to call it **with `1337` as its first argument**.

The calling convention says the first argument goes in `rdi` --- the same register the function pointer is in (because it's passed in as the first argument _to your solve function_).
This means trouble:

- If you set `rdi` to `1337`, you'll clobber the pointer (and then `call rdi` will try to call a function at address `1337` and crash)
- If you `call rdi` with `rdi` intact, you'll pass the function pointer as the first argument instead of `1337`, and you won't get the flag.

This is an instance of a fundamental reality when dealing with assembly: your program has to share the same set of registers, and one function might want `rdi` for some different purpose than another.
To resolve this contention, caller functions typically will `push` important registers to their local stack frame before invoking callees.

Anyways, here, the fix is simple: you have to use another register for the `call`, for example, by moving the callback function address into `rax` and then invoking `call rax`.
That will free `rdi` for your argument!
