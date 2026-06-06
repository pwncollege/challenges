You've practiced _caller_-saved registers, and now we'll cover _callee_-saved ones.
The callee-saved registers (`rbx`, `rbp`, `r12`, `r13`, `r14`, `r15`) come with the promise of being returns unclobbered by the callee.
When a function uses one of them, it is _borrowing_ it from whoever called it, and it must return it in exactly the condition it was found.
This is what lets a caller keep long-lived values in `rbx`/`r12`-`r15` across a call and trust they'll still be there afterward.

The rule is, when your function wants to use these registers, _save (push) them on entry to your function, restore (pop) them before you `ret`_.

This level puts you on the callee side.
Your `solve` is called as `solve(check_callee_clobbered)` (the pointer is in `rdi`), and your caller has live values sitting in `rbx`, `r12`, `r13`, `r14`, `r15` that it expects back untouched.

Your job:

1. Save off all the callee-saved registers.
2. Clobber them all by setting them to `0x1337`.
3. Call `check_callee_clobbered`, which confirms you clobbered them.
4. Restore the callee-saved registers.
5. `ret`.

The challenge then checks that `rbx`, `r12`-`r15` came back exactly as it left them.
Borrow them, give them back, and claim the flag.
