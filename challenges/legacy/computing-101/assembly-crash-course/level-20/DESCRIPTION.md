We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with control flow manipulation. This involves using instructions to both indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

In a previous level, you computed the average of 4 integer quad words, which was a fixed amount of things to compute. But how do you work with sizes you get when the program is running?

In most programming languages, a structure exists called the for-loop, which allows you to execute a set of instructions for a bounded amount of times. The bounded amount can be either known before or during the program's run, with "during" meaning the value is given to you dynamically.

As an example, a for-loop can be used to compute the sum of the numbers 1 to n:

```plaintext
sum = 0
i = 1
while i <= n:
    sum += i
    i += 1
```

Please compute the average of `n` consecutive quad words, where:
- `rdi` = memory address of the 1st quad word
- `rsi` = `n` (amount to loop for)
- `rax` = average computed
