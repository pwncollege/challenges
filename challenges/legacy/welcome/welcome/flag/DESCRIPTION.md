So far, the challenges have been giving you flags directly.
In this challenge, you will learn that the flag actually lives in the `/flag` file.
Your real goal, in any challenge, is to get the contents of this file through any means necessary, even if the challenge program does not do it on purpose.

You might try to just read the `/flag` file on your own.
Unfortunately for you, you are executing as the `hacker` user and `/flag` is only readable by the `root` user, so you cannot access it.
In the previous challenges, the challenge program itself (e.g., `/challenge/solve`), which runs as the `root` user (and, thus, can read the flag), read this file and printed its contents, but this level is harder.

Like many of the other challenges on the platform, this challenge's `/challenge/solve` program will not read the flag file directly.
However, it will make the flag world-readable when you run it!
After that, you will need to read `/flag` yourself (e.g., using `cat /flag` or a text editor), and submit its contents as the solution.
