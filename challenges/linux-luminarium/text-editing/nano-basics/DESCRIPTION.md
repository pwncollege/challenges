`nano` is a text editor that runs inside your terminal.
Open a file by passing its path:

```console
hacker@dojo:~$ nano FILE
```

Move around with the arrow keys, type to insert text, and use Backspace or Delete to remove text.
Nano lists its most important shortcuts along the bottom of the screen.
There, `^` means the Ctrl key, so `^O` means Ctrl-O and `^X` means Ctrl-X.

Ctrl-O writes your changes to the file.
Press Enter to confirm the filename, then press Ctrl-X to exit Nano and return to your shell.

Open `/home/hacker/README.txt` in Nano and add this exact second line:

```text
Editing in nano works!
```

Keep the original first line, save the file, exit Nano, and run `/challenge/check` to get the flag.
