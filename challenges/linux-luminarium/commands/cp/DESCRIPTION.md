But what if you want to keep the original file? You can do so with the `cp` command.
The usage is the same as with `mv`, but it will keep the source file.
The command is `cp SOURCE DESTINATION`: the first argument is the existing file, and the second is where the copy should be created.

This challenge wants you to copy the `/flag` file to `/tmp/hack-the-planet` (do it)!
When you're done, run `/challenge/check`, which will check things out and give the flag to you.

----
**NOTE:**
When a `cp` destination is a directory, `cp` places the copy inside it using the source file's name.
For this challenge, `/tmp/hack-the-planet` should name the copied file itself, rather than an existing directory.
