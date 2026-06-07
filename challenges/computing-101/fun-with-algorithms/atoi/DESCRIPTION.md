Your two-digit `atoi` did `first * 10 + second`.
What if there are more than two digits?
Of course, you'd keep a running total, and for each new digit do `total = total * 10 + digit`.
That repetition is a _loop_, which you've read before, but will write here!

Read the digits left to right:

```
"123":
  total = 0
  '1':  total =  0*10 + 1  =   1
  '2':  total =  1*10 + 2  =  12
  '3':  total = 12*10 + 3  = 123
```

You would do this until the end of the string, which, by the convention of the C programming language (and used here), is represented by a byte with a value of 0x00 (that is, binary `00000000` or decimal _value_ 0).
Note that this is distinct from the character '0', which, again, has a value of `0x30` (binary `00110000`).

So, your loop is: look at the next byte, if it's `0`, jump beyond the loop (look back at the [Looping](https://pwn.college/computing-101/control-flow/loop) challenge for reference), otherwise multiply the total by `10`, call `atoi_digit` to convert the digit, and add it to the total, then loop back to the head of the loop.
Easy!

Your `atoi` receives a pointer to the string in `rdi` and must return the integer value in `rax`.
Loop the digits, return the number, and score!
