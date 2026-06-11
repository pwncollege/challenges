Let's try something a bit trickier!
You've piped output between programs with `|`, but so far, this has just been between one command's output and a different command's input.
But what if you wanted to send the output of several programs to one command?
There are a few ways to do this, and we'll explore a simple one here: redirecting output from your script!

As far as the shell is concerned, your script is just another command.
That means you can redirect its input and output just like you did for commands in the [Piping](/linux-luminarium/piping) module!

For example, you can pipe the output of your script into another command:

```console
hacker@dojo:~$ cat script.sh
#!/bin/bash
echo PWN
echo COLLEGE
hacker@dojo:~$ ./script.sh | cat
PWN
COLLEGE
```

All of the various redirection methods work: `>` for stdout, `2>` for stderr, `<` for stdin, `>>` and `2>>` for append-mode redirection, `>&` for redirecting to other file descriptors, and `|` for piping to another command.

In this level, we will practice piping (`|`) the output from your executable script into another program. Specifically, create an executable script that calls `/challenge/pwn` followed by `/challenge/college`, and pipe the output of your script into a single invocation of `/challenge/solve`!
