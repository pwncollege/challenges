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
- Your `atoi` clobbers the caller-saved registers as it runs, so keep your loop counter, running total, and array base in callee-saved registers and preserve them across the call --- the same discipline you practiced in the [callee-saved-registers](/computing-101/control-flow) level.

Build and submit as before:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

Sum them all, return the result, and the flag is yours.
