We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with memory. This will require you to read or write to things stored linearly in memory. If you are confused, go look at the linear addressing module in 'ike. You may also be asked to dereference things, possibly multiple times, to things we dynamically put in memory for your use.

Up until now, you have worked with registers as the only way for storing things, essentially variables such as 'x' in math.

However, we can also store bytes into memory!

Recall that memory can be addressed, and each address contains something at that location. Note that this is similar to addresses in real life!

As an example: the real address '699 S Mill Ave, Tempe, AZ 85281' maps to the 'ASU Brickyard'. We would also say it points to 'ASU Brickyard'. We can represent this like:

```
['699 S Mill Ave, Tempe, AZ 85281'] = 'ASU Brickyard'
```

The address is special because it is unique. But that also does not mean other addresses can't point to the same thing (as someone can have multiple houses).

Memory is exactly the same!

For instance, the address in memory where your code is stored (when we take it from you) is `0x400000`.

In x86, we can access the thing at a memory location, called dereferencing, like so:

```
mov rax, [some_address]        <=>     Moves the thing at 'some_address' into rax
```

This also works with things in registers:

```
mov rax, [rdi]         <=>     Moves the thing stored at the address of what rdi holds to rax
```

This works the same for writing to memory:

```
mov [rax], rdi         <=>     Moves rdi to the address of what rax holds.
```

So if `rax` was `0xdeadbeef`, then `rdi` would get stored at the address `0xdeadbeef`:

```
[0xdeadbeef] = rdi
```

Note: Memory is linear, and in x86_64, it goes from `0` to `0xffffffffffffffff` (yes, huge).

Please perform the following: Place the value stored at `0x404000` into `rax`. Make sure the value in `rax` is the original value stored at `0x404000`.
