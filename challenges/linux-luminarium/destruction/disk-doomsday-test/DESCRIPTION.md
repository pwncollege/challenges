The available space in `/home/hacker` in this container is deliberately limited.
In this level you will clog up `/home/hacker` with so much junk that even a tiny 1 megabyte file can't be created.
When this happens, your workspace becomes unusable.
We'll practice inducing this in this challenge, and then expand on it a bit later.

How to fill the disk?
There are so many ways.
Here, we'll teach you the `yes` command!

```
hacker@dojo:~$ yes | head
y
y
y
y
y
y
y
y
y
y
hacker@dojo:~$
```

The `yes` outputs `y` over and over forever.
The typical usage is to automate confirmation prompts ("Are you sure you want to delete this file?") using piping, but we'll use it here to make a massive file full of "y" lines.
Just redirect `yes` to a file in your home directory, and you'll fill your disk!

This challenge forces you to fill the disk and then clean up.
The process:

1. Fill your disk.
2. Run `/challenge/check`. It will attempt to create a 1 megabyte temporary file. If that fails, you pass the first stage and the checker will ask you to free the space.
3. Delete the file you made (with `rm`) to clear up the space.
4. Run `/challenge/check` a second time.  If it can now create the temporary file (i.e., you successfully cleaned up your home directory), you’ll receive the flag.

----
**Why two stages?**
This challenge temporarily replaces `/home/hacker` with a size-limited workspace for the exercise.
Your normal persistent home is left untouched and returns when you leave the challenge.
If we let you keep your normal home full, your pwn.college would stop working.
This is _by far_ the most common cause of weird issues on pwn.college!

**HELP IT BROKE!**
If you lose your connection after filling the temporary workspace, restart the challenge to reset it.
To earn the flag, you must fill and clean up the workspace in the same challenge instance.
