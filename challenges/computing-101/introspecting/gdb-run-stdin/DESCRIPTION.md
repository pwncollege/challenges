In the previous level, you passed command-line arguments through gdb's `run`.
Programs can also read from stdin, and gdb lets you redirect stdin when you run the inferior.
The syntax is the same redirection you've seen in the shell, but it goes after `run` inside gdb:

```text
(gdb) run < /path/to/input
```

In this challenge, `/challenge/debug-me` reads its required input from `/challenge/secret`.
Run it under gdb with `/challenge/secret` redirected into stdin, read the secret number it prints, and submit that number with `/challenge/submit-number`.
