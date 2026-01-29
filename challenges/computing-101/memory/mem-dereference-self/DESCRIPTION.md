In the previous level, you dereferenced `rax` to read data into `rdi`.
The interesting thing here is that our choice of `rax` was pretty arbitrary.
We could have used any other pointer, even `rdi` itself!
Nothing stops you from dereferencing a register to overwrite its own content with the dereferenced value!

For example, here is us doing this exact thing with `rax`.
I've annotated each line with comments:

```assembly
mov [133700], 42
mov rax, 133700  # after this, rax will be 133700
mov rax, [rax]   # after this, rax will be 42
```

Throughout this snippet, `rax` goes from being used as a pointer to being used to hold the data that's been read from memory.
The CPU makes this all work!

In this challenge, you'll explore this concept.
Rather than initializing `rax`, as before, we've made `rdi` the pointer to the secret value!
You'll need to dereference it to load that value into `rdi`, then `exit` with that value as the exit code.
Good luck!
