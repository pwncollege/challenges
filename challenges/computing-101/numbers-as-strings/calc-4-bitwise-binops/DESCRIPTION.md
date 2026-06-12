Now, let's teach the calculator the *bitwise* operators!

Every operator so far has been arithmetic. The next three combine their operands bit by bit, and you've met all of them back in `assembly-assortment`:

- `^` is XOR: each result bit is `1` when *exactly one* input bit is `1`.
- `|` is OR: each result bit is `1` when *either* input bit is `1`.
- `&` is AND: each result bit is `1` only when *both* input bits are `1`.

Add three more branches to your dispatch --- `'^'` → `xor`, `'|'` → `or`, `'&'` → `and` --- alongside `'+'`, `'-'`, and `'*'`.
Any operator you still don't recognize makes you quit with a nonzero exit code.

A bitwise result is just a 64-bit number, so you print it like every other answer: feed it to your signed `itoa` and `write` the text.

```
"12"  ->  atoi  ->  12     (0000 1100)
"10"  ->  atoi  ->  10     (0000 1010)
12  ^  10  =  6            (0000 0110)
12  |  10  =  14           (0000 1110)
12  &  10  =  8            (0000 1000)
```

Two of these are special to the shell --- `|` pipes commands together and `&` runs one in the background --- so quote them when you run your program by hand (`^` is fine bare):

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 12 '|' 10
14
hacker@dojo:~$ /challenge/check prog
```

Add the three bitwise branches.
