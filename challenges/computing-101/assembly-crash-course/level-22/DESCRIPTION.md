We will be testing your code multiple times in this level with dynamic values! This means we will be running your code in a variety of random ways to verify that the logic is robust enough to survive normal use.

In this level, you will be working with functions! This will involve manipulating the instruction pointer (rip), as well as doing harder tasks than normal. You may be asked to use the stack to store values or call functions that we provide you.

In previous levels, you implemented a while loop to count the number of consecutive non-zero bytes in a contiguous region of memory.

In this level, you will be provided with a contiguous region of memory again and will loop over each performing a conditional operation till a zero byte is reached. All of which will be contained in a function!

A function is a callable segment of code that does not destroy control flow.

Functions use the instructions "call" and "ret".

The "call" instruction pushes the memory address of the next instruction onto the stack and then jumps to the value stored in the first argument.

Let's use the following instructions as an example:
```
0x1021 mov rax, 0x400000
0x1028 call rax
0x102a mov [rsi], rax
```

1. `call` pushes `0x102a`, the address of the next instruction, onto the stack.
2. `call` jumps to `0x400000`, the value stored in `rax`.

The "ret" instruction is the opposite of "call".

`ret` pops the top value off of the stack and jumps to it.

Let's use the following instructions and stack as an example:

```
                            Stack ADDR  VALUE
0x103f mov rax, rdx         RSP + 0x8   0xdeadbeef
0x1042 ret                  RSP + 0x0   0x0000102a
```

Here, `ret` will jump to `0x102a`.

Please implement the following logic:
```plaintext
str_lower(src_addr):
  i = 0
  if src_addr != 0:
    while [src_addr] != 0x00:
      if [src_addr] <= 0x5a:
        [src_addr] = foo([src_addr])
        i += 1
      src_addr += 1
  return i
```

`foo` is provided at `0x403000`. `foo` takes a single argument as a value and returns a value.

All functions (`foo` and `str_lower`) must follow the Linux amd64 calling convention (also known as System V AMD64 ABI):
[System V AMD64 ABI](https://en.wikipedia.org/wiki/X86_calling_conventions#System_V_AMD64_ABI)

Therefore, your function `str_lower` should look for `src_addr` in `rdi` and place the function return in `rax`.

An important note is that `src_addr` is an address in memory (where the string is located) and `[src_addr]` refers to the byte that exists at `src_addr`.

Therefore, the function `foo` accepts a byte as its first argument and returns a byte.
