In the previous module, you wrote assembly programs and built them into executables.
But what if someone gives you a program and you want to understand what it does?
This is where **disassembly** comes in: the process of converting the binary machine code in an executable _back_ into human-readable assembly instructions.

Though you will learn to use vastly more powerful tooling later in your journey, we will start with one of the most common tools for disassembly: `objdump`.
Given a binary, `objdump -d` will disassemble the executable sections and show you the assembly instructions:

```console
hacker@dojo:~$ objdump -d -M intel /tmp/your-program

/tmp/your-program:     file format elf64-x86-64


Disassembly of section .text:

0000000000401000 <_start>:
  401000:	48 c7 c7 39 05 00 00 	mov    rdi,0x539
  401007:	48 c7 c7 00 00 00 00 	mov    rdi,0
  40100e:	48 c7 c0 3c 00 00 00 	mov    rax,0x3c
  401015:	0f 05                	syscall
```

There are a few things to note here.
First, by default, `objdump` uses the wrong assembly syntax, which is why we pass the `-M intel` option.
Don't forget this option!
Viewing assembly in non-Intel syntax can be confusing and harmful for your health.

Second, `objdump` displays the raw bytes of each instruction (e.g., the _hexadecimal_ values `0f 05` is the `syscall` instruction) alongside the human-readable assembly.
These are the actual values that are stored in computer memory to represent the instructions.
For mathematical reasons, these are represented in "base 16" (hexadecimal) rather than the "base 10" (decimal) that we are used to counting with.
If that does not make sense, please run through the first half or so of the [Dealing with Data](/fundamentals/data-dealings) module and then come back here!

Third, the values that are being moved into registers are _also_ represented as hexadecimal.
This can make it slightly tricky to understand what the program is doing.
Above, we can see that it is setting `rax` to the hexadecimal value `0x3c`, which is `60` in decimal and, thus, is our familiar syscall number of `exit`!
Right before that, it sets `rdi` to `0`, which will be the exit code of the program.

But interestingly, right before _that_, it sets `rdi` to `0x539`, which we can't really observe from the outside because it's overwritten to `0` immediately.
While this "secret" is benign, by reading the code of software, we can extract many different such secrets, some of which are security relevant!

We'll practice this secret extraction in this challenge, using a binary at `/challenge/disassemble-me`.
Use `objdump` to disassemble it and find the number being loaded into `rdi` before it's wiped out.
Then, submit that number using `/challenge/submit-number`.
The number will be displayed in hexadecimal in the disassembly, but `/challenge/submit-number` accepts both hexadecimal (e.g., `0x539`) and decimal (e.g., `1337`) values.
Good luck!
