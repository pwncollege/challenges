You can turn a single digit character into its value with `atoi_digit`: subtract `'0'`.
Now write the full `atoi` --- this level's `solve` --- which turns a *whole* number like `"12345"` into an integer by looping that digit-decode across every character.

Read the digits left to right and build the number up one at a time.
Start with a running total of `0`; for each digit, multiply the total by 10 (to shift the digits you already have one place to the left) and add the new digit's value:

```
"123":
  total = 0
  '1':  total =  0*10 + 1  =   1
  '2':  total =  1*10 + 2  =  12
  '3':  total = 12*10 + 3  = 123
```

So each pass of your loop does `atoi_digit` on the current character (read the byte, subtract `'0'`), folds it into the total with a multiply-and-add, and advances to the next character.
You know you've reached the end of the string when you hit the NUL terminator: the `0x00` byte that marks where the text stops.
For now, assume the input is a clean run of decimal digits, followed by that NUL.

Your `solve` receives a pointer to the string in `rdi` and must return the integer value in `rax`.

Build and submit as before:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

Loop the digits, return the number, and the flag is yours.
