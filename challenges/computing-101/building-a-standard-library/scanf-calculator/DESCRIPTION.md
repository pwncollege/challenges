Your calculator already knows arithmetic, your formatter knows output, and your scanner now knows input.
Combine them into a program that reads one calculation from standard input.

Print `calc> `, then use your `scanf` with `"%d %s %d"` to read two numbers and the operator between them.
Support `+`, `-`, and `*`.
Print the signed decimal result followed by a newline, then exit successfully.
The operands are between `-10000` and `10000`, and one `read` supplies the complete valid expression.

Reuse your scanner and the decimal output code from your formatter.
Export `.global _start` as the program's entry point.

```console
hacker@dojo:~$ as --64 calculator.s -o calculator.o
hacker@dojo:~$ ld calculator.o -o calculator
hacker@dojo:~$ ./calculator
calc> 12 * -3
-36
hacker@dojo:~$ /challenge/check calculator
```
