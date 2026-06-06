Now do something with *all* of them.

You have `nums` (in `rdi`) and `count` (in `rsi`).
Walk the array from `nums[0]` to `nums[count-1]`, convert each string with your `atoi`, and add the values into a running total.
Return that total in `rax`.

```
sum = 0
for i in 0 .. count-1:
    sum += atoi(nums[i])
return sum
```

This is the same kind of loop you've written before, except the body now does real work: each iteration loads `nums[i]` (a pointer), converts the string it points at, and adds the value to your accumulator.

Two things to keep straight:
- Each pointer is 8 bytes, so stepping from `nums[i]` to `nums[i+1]` moves 8 bytes along the array (`[rdi + i*8]`).
- Your `atoi` clobbers registers as it runs, so keep your loop counter, your running total, and the array base in registers that survive across it (the callee-saved registers: `rbx`, `r12`-`r15`), and remember to save and restore them.

Sum them all, return the result, and the flag is yours.
