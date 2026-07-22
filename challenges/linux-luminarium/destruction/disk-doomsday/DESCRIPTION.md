In this challenge, `/home/hacker` is backed by a small temporary filesystem.
You will clog it with so much junk that even a tiny 1 megabyte file can't be created.
Then you will clean up the junk and restore the available space.

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

The `yes` command outputs `y` over and over forever.
The typical usage is to automate confirmation prompts ("Are you sure you want to delete this file?") using piping, but we'll use it here to make a massive file full of "y" lines.
Just redirect `yes` to a file in your home directory, and it will keep growing until the temporary filesystem fills up!

This challenge forces you to fill the disk and then clean up.
The process:

1. Fill your disk.
2. Run `/challenge/check`. It will attempt to create a 1 megabyte temporary file. If that fails, you pass the first stage and the checker will ask you to free the space.
3. Delete the file you made (with `rm`) to clear up the space.
4. Run `/challenge/check` a second time.  If it can now create the temporary file (i.e., you successfully cleaned up your home directory), you’ll receive the flag.

----
**NOTE:**
Your existing home-directory files will not be available here, and files you save here will not persist after the challenge ends.

**Why two stages?**
Filling a filesystem is only half the exercise.
The second stage teaches you to clean up after exhausting a system resource, even though this sandbox keeps the experiment away from your persistent home directory.
