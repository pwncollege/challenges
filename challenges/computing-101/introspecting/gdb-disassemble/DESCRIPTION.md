In the previous level, we ran the `disassemble` command for you after you started the program.
Now it's your turn!

After starting the program with `starti`, you will need to run the `disassemble` command yourself:

```gdb
(gdb) starti
...
(gdb) disassemble
Dump of assembler code for function main:
=> 0x0000000000401000 <+0>:     mov    rdi,0x539
   0x0000000000401007 <+7>:     mov    rdi,0x0
   0x000000000040100e <+14>:    mov    rax,0x3c
   0x0000000000401015 <+21>:    syscall
End of assembler dump.
```

Read the output to find the secret number, then submit it with `/challenge/submit-number`.
