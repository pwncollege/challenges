Now, let's teach the calculator to subtract!

Add a second branch on the operator byte: if it's `'-'`, `sub` the right operand from the left instead of adding.
Everything else is the same dispatch you already wrote --- `'+'` adds, `'-'` subtracts, and any other operator still makes you quit with a nonzero exit code.

The one thing to watch: a difference can be **negative**.

```
"3"   ->  atoi  ->   3
"10"  ->  atoi  ->  10
3  -  10  =  -7
-7   ->  itoa  ->  "-7"
```

That's exactly the case your signed `itoa` already handles --- it writes the leading `'-'` and the magnitude for you.
So feed the difference straight into the same `itoa` you've been using, and the sign takes care of itself.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 3 - 10
-7
hacker@dojo:~$ /challenge/check prog
```

Add the subtract branch and print the signed result.
