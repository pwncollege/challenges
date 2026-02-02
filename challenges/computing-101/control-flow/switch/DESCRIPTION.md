In the previous challenge, you reverse-engineered `cmp`/`jne` pairs to recover a password.
That technique checks each possibility one by one: compare, branch, compare, branch...
But what if a program needs to branch to one of _many_ different destinations based on a single value?

There's a more efficient approach: a **jump table**.
A jump table is an array of addresses stored in memory, one for each possible destination (called a **case**).
Instead of comparing the input against every possibility, the program uses the input value as an _index_ into the table, loads the address stored at that position, and jumps to it.
This pattern is called a **switch**, and it's a fundamental building block in programs.

In the disassembly, you'll see something like:

```asm
xor    eax, eax                  ; zero out rax
mov    al, BYTE PTR [rcx]        ; load the character into the low byte of rax
mov    rax, [rax*8+0x1234000]    ; load a stored address from the jump table at 0x1234000
jmp    rax                       ; jump to it
```

You've seen `dil` (the low byte of `rdi`) before, and `al` is the same idea for `rax`.
Writing to `al` only changes the lowest 8 bits, leaving the rest of `rax` intact.
That's why the code first zeros `rax` with `xor eax, eax`: it ensures the upper bytes are `0`, so after `mov al, [rcx]`, `rax` holds just the character's value (0--255).

The character's value directly indexes a table of 256 entries (one per possible byte value).
Each entry is an **8 byte** address pointing to code for that case.
In this way, the program implements conditional logic _without any conditional control flow_!

This challenge (at `/challenge/reverse-me`) has 256 possible cases, with only one of them (corresponding to an alphanumeric character) being different than the others.
Look at the jump table (you'll have to look at a lot of entries...), look at the program to understand how to influence the index, and get the flag!

----
**NOTE:**
Though you should look at the disassembly using `objdump -d -M intel /challenge/reverse-me`, objdump will try to interpret the jump table data as assembly instructions, which will result in garbage.
Ignore that section of the disassembly; you'll need to look at that data in gdb, instead.

**HINT:**
You'll likely want to use gdb extensively in this challenge, and `x/a` will be your friend.
For example, if you are in gdb at the instruction `mov rax, [rax*8+0x1337000]` (note, your address will differ), you can examine the jump table entries:

```gdb
(gdb) print $rax
1
(gdb) x/a $rax*8+0x1337000
0x1337008:  0x400100
(gdb) x/a 2*8+0x1337000
0x1337010:  0x400100
(gdb) x/a 98*8+0x1337000
0x1337310:  0x400200
(gdb)
```

**HINT:**
You can also print out *several* jump table entries at the same time:

```gdb
(gdb) x/3a 0x1337000
0x1337000:  0x400100
0x1337008:  0x400100
0x1337010:  0x400100
(gdb)
```
