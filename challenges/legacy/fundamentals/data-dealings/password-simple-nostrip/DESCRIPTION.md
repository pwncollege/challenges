The previous challenges were quite simple, as is this one.
But it does one thing slightly differently: it does not ignore the Enter that you press on the terminal when entering your password.
This causes your `entered_password` to contain a newline, and since `correct_password` has no newline, the comparison fails!

This sort of stuff --- errant delimiters in data --- happens ALL the time and can lead to crazy amounts of lost time.
There are a few ways to get around it in this level:

1. Look into ways to terminate your terminal input _without_ pressing Enter.
   This is super searchable online!
2. Recall, from the Linux Luminarium, how to redirect an `echo` (with arguments to disable newlines) to the stdin of `/challenge/runme`.
3. Create a file without a newline, and remember your Linux Luminarium to redirect the file to stdin of `/challenge/runme`.

Good luck!
