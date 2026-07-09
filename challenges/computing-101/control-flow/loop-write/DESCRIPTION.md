In the previous challenge, you recognized a loop in a program someone else wrote.
Now you will write one yourself.

A loop needs three pieces of state: where the current work is, how much progress has been made, and a test that decides when the loop is finished.
For a string, the natural finish line is the null terminator: the `0` byte after the last character.
Each trip through the loop checks the current byte, advances to the next byte, updates the count, and jumps back to repeat.

Write a program that computes the length of `argv[1]` and exits with that length as its exit code.
Your program must inspect the string one byte at a time and use a backward jump to repeat the loop.

For example, if the argument is `pwn`, your program should exit with code `3`.
If the argument is empty, it should exit with code `0`.

Submit it to `/challenge/check`, and get the flag!
