Up to now, your `solve` received a single string.
Real programs usually get *several* values at once.
When you run `./program 11 22 33`, the operating system hands the program an array called `argv`: a contiguous block of *pointers*, one per argument, each pointing at a NUL-terminated string.

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
