Now, let's _decode_ some hex, rather than encoding it.
Can you figure out what the program needs?

---
**NOTE:**
One of the toughest parts of this challenge is to send raw binary data to it stdin.
There are a few ways to do this:

1. Write a python script to output data to stdout and pipe that to the challenge's stdin!
   This would involve using the raw byte interface to stdout: `sys.stdout.buffer.write()`.
2. Write a python script to run the challenge and interact with it directly.
   Our recommendation is to use pwntools for this: `import pwn`, `p = pwn.process("/challenge/runme")`, `p.write()`, and `p.readall()`.
   A pwn.college alumni has created an awesome [pwntools cheat sheet](https://gist.github.com/anvbis/64907e4f90974c4bdd930baeb705dedf) that you may reference.
3. For an increasingly hacky solution, `echo -e -n "\xAA\xBB"` will print out bytes to stdout that you can pipe.
