In the previous challenges, you used `setz` to capture a comparison result as a `0` or `1` in `dil`, then passed that directly as your exit code.
That was a neat trick --- but it has limitations.
What if you want your program to take entirely different _actions_ depending on whether the values were equal?

This is where **conditional jumps** come in.
Instead of recording the comparison result into a register, you can tell the CPU to _jump_ to a different part of your code based on the outcome of the `cmp`.
The most useful conditional jump for our purposes is `jne` (**J**ump if **N**ot **E**qual):

```asm
cmp BYTE PTR [rax], 'p'
jne fail
```

After the `cmp`, if the values were _not_ equal, the CPU jumps to the location labeled `fail`.
He terminology used for this is that it "takes the branch" (in the road/code).
If the values _were_ equal, the CPU simply continues to the next instruction.
The terminology used for this is behavior of _not_ taking the branch that it "falls through" to the next instruction.

Under the hood, `jne` checks the Zero Flag (ZF) that `cmp` set: `jne` jumps when ZF = 0 (meaning the subtraction result was non-zero, i.e., the values differed).
There's also `je` (**J**ump if **E**qual), which does the opposite: it jumps when the values _are_ equal.

But what is `fail`?
It's a **label** --- a name you give to a location in your code.
Labels don't generate any machine instructions; they just mark a spot that jump instructions can refer to.
You define a label by writing its name followed by a colon:

```asm
fail:
  mov rdi, 1
  mov rax, 60
  syscall
```

The assembler resolves the label to an address, so `jne fail` becomes something like `jne <address>` in the actual machine code.
You can name labels almost anything (`fail`, `error`, `done`, `loop`, etc.), but the name should describe what happens at that location.

With conditional jumps, your programs can now have two different _paths_ of execution:

```
main:
  [load and compare]
  jne fail          ← jump to fail if NOT equal

success:
  mov rdi, 0
  mov rax, 60
  syscall

fail:
  mov rdi, 1
  mov rax, 60
  syscall
```

If the comparison succeeds (the values are equal), execution falls through to the success path and exits with `0` --- the standard "success" exit code for Linux programs.
If the comparison fails (the values are not equal), execution jumps to the `fail` label and exits with `1` --- indicating program failure.

Of course, this is a simple example, but we'll start simple!
The challenge: write a program that checks whether the first character of `argv[1]` is `'p'`, using conditional jumps instead of `setz`:

1. Load the `argv[1]` pointer from `[rsp+16]` into a register.
2. Compare `BYTE PTR` at that address against `'p'`.
3. `jne fail` --- jump to the failure case if the characters aren't equal.
4. Write the "fall-through" success case (`exit(0)`).
5. Define the `fail:` label and write the fail case (`exit(1)`).

The tricky thing is that your success case (jump _not_ taken) is between your `jne` instruction and the fail case that the `jne` instruction refers to.
This can take a bit to wrap your head around, but you'll get used to it!
