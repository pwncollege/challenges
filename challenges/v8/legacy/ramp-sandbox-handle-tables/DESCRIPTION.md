The V8 sandbox stores boundary-facing capabilities through handle tables instead of raw process pointers.
Changing the right handle can redirect a boundary object while staying inside the heap cage.

In this level, the harness gives you read and write access to two modeled boundary objects.
Copy the trusted handle that makes the recipient dispatch to the win target, then run `/challenge/run` with your solve file to get the flag.
