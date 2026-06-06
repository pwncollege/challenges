Up to now, your `solve` received a single string.
Real programs usually get *several* values at once, as `argv` --- the array of argument pointers you've already walked off the stack back in the [stack](/computing-101/the-stack) module.
This time the challenge hands that array straight to your `solve`: a contiguous block of *pointers*, one per argument, each pointing at a NUL-terminated string.

In this challenge your `solve` receives such an array, using the standard argument convention:
- `rdi` holds `nums` --- the address of the array of string pointers.
- `rsi` holds `count` --- how many strings are in the array.

Each entry `nums[i]` is itself a *pointer* to a number string, so getting to a number is now a two-step dereference: first load the pointer out of the array, then read the digits it points at.

```
nums:   rdi -> [ ptr0 ][ ptr1 ][ ptr2 ] ...
                  |
       ptr0 ------+--> "11"
```

To grab the first string's pointer:

```
mov rdi, [rdi]      ; rdi = nums[0], the pointer to the first string
```

For this level, just convert that first string and return its value.
Bring the `atoi` you wrote in the previous levels with you: point it at `nums[0]`, and return the result in `rax`.

Build and submit as before:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

Pick out the first number, return it, and the flag is yours.
