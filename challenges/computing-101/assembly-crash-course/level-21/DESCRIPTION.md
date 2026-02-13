In this level, you will be working with control flow manipulation. This involves using instructions to both indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

We will be testing your code multiple times in this level with dynamic values! This means we will be running your code in a variety of random ways to verify that the logic is robust enough to survive normal use.

In previous levels, you discovered the for-loop to iterate for a *number* of times, both dynamically and statically known, but what happens when you want to iterate until you meet a condition?

A second loop structure exists called the while-loop to fill this demand. In the while-loop, you iterate until a condition is met.

As an example, say we had a location in memory with adjacent numbers and we wanted to get the average of all the numbers until we find one bigger or equal to `0xff`:

```plaintext
average = 0
i = 0
while x[i] < 0xff:
  average += x[i]
  i += 1
average /= i
```

Using the above knowledge, please perform the following:

Count the consecutive non-zero bytes in a contiguous region of memory, where:
- `rdi` = memory address of the 1st byte
- `rax` = number of consecutive non-zero bytes

Additionally, if `rdi = 0`, then set `rax = 0` (we will check)!

An example test-case, let:
- `rdi = 0x1000`
- `[0x1000] = 0x41`
- `[0x1001] = 0x42`
- `[0x1002] = 0x43`
- `[0x1003] = 0x00`

Then: `rax = 3` should be set.
