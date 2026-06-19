There are two dangers to UDP: first, it is often used in places where people are already cutting corners for performence's sake.
Second, it forces the programmer to keep track of sessions explicitly.
This combination can cause security issues.

In this challenge, one side of the connection can confuse a non-trusted connection for a trusted connection, and print the flag.
Can you trigger this confusion?

----

**NOTE:**
In this level, the flag will just be printed to the console when you trigger the confusion.
We'll work on realistically exfiltrating it later.
