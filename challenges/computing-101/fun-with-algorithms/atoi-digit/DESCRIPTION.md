Computers receive a lot of their input as *text*.
When you pass `12345` to a program as a command-line argument, your code doesn't receive the *number* 12345 --- it receives five separate ASCII bytes: `'1'`, `'2'`, `'3'`, `'4'`, `'5'`.
The CPU can't add or multiply that text directly; first, someone has to turn those characters into the numbers they represent.
That job is traditionally done by a function called `atoi` (ASCII to integer) --- and we'll build it from the ground up, starting here with a single digit.

The key insight is how digits are encoded.
You've seen ASCII in prior levels, and we'll talk about ASCII _numbers_ (the text encoding of numerical values) here.
In ASCII, the character `'0'` is the byte `0x30`, `'1'` is `0x31`, and so on up to `'9'` at `0x39`.
The digits are consecutive, so the *value* of a digit character is simply the character minus `'0'`:

```
'7'  ->  0x37 - 0x30  =  7
```

In this level, you must implement a function that converts a text string containing one digit into the number.
Your function (which must be called `atoi_digit`) receives a pointer in `rdi` to a single digit character, and must return that digit's value (`0` through `9`) in `rax`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Decode the digit, return its value, and grab the flag.
