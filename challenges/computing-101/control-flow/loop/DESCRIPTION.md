So far, every control flow pattern you've seen executes in a straight line: compare, branch, done.
But what if you need to repeat the same operation many times?
That's what a **loop** is: a sequence of instructions that jumps _backward_ to repeat itself.

In this challenge, `/challenge/reverse-me` compares `argv[1]` against the password using a loop:

```asm
loop:
  mov    al, BYTE PTR [rsi]       ; load next password character
  cmp    al, BYTE PTR [rdi]       ; compare against next argv[1] character
  jne    fail                     ; mismatch → jump to fail
  cmp    al, 0x0                  ; reached the null terminator?
  je     success                  ; yes → all characters matched!
  inc    rdi                      ; **inc**rement rdi to advance to next argv[1] character
  inc    rsi                      ; **inc**rement rsi to advance to next password character
  jmp    loop                     ; jump back to the top — repeat!
```

The key instruction is `jmp loop` at the bottom.
Unlike `jne` (which only jumps when a condition is met), `jmp` **unconditionally** always jumps.
By jumping backward to the `loop` label, the program re-executes the same comparison logic on the _next_ pair of characters.
The loop terminates when either a mismatch is found (`jne fail`) or the null terminator is reached at the end of the string after the other characters are successfully matched to the password (`je success`).

This is the fundamental pattern behind every `for` loop, `while` loop, and string operation you'll ever encounter in compiled code.

Analyze the binary, figure out the password, and get the flag!
