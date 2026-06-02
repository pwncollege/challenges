The challenge in the previous level inherited your interactive shell's environment both in and outside of gdb.
In reality, the differences in environment are often more significant between your local setup and the target you're analyzing.
The binary you're debugging from your shell and the same binary running as a service, a cron job, or a remote script would see completely different environments (different `HOME`, different `PATH`, a different _set_ of variables entirely).

This level explores this concept a bit more.
In this level, the `gdb` wrapper sets its own environment rather than inheriting it from your shell, and the challenge, when run directly forces you to do the same, requiring an environment with only a single variable.
For example:

```console
hacker@dojo:~$ /challenge/program
You're running me with 8 environment variables, but I need exactly 1! Clear the environment and set one variable, then rerun me!
hacker@dojo:~$ /challenge/program
```

How do you clear the environment?
You can do so with the `env` command, which we've used before to print out all exported environment variables in the [Linux Luminarium](/linux-luminarium/variables).
The `env` command can also be used as a _wrapper_ to carefully control the environment of a program.
For example, you can clear the child program's environment completely using `env -i`:

```console
hacker@dojo:~$ env -i /challenge/program
You're running me with 0 environment variables, but I need exactly 1! Clear the environment and set one variable, then rerun me!
hacker@dojo:~$ /challenge/program
```

You can also set variables after clearing the environment:

```console
hacker@dojo:~$ env -i PWN=COLLEGE HACK=PLANET /challenge/program
You're running me with 2 environment variables, but I need exactly 1! Clear the environment and set one variable, then rerun me!
hacker@dojo:~$ /challenge/program
```

This allows you to have very finegrained control over your environment.
In this challenge, you'll use this finegrained control to line up addresses in a slightly more realistic setting, but keep the capability in mind for other situations!
