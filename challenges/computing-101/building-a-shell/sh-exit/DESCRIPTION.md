Your shell can keep running until its input ends.
Now give it a command that deliberately ends the session: `exit`.

This is a *builtin*: work performed by the shell itself.
An external program runs in a child, so ending that child would leave the parent shell running.

When the command is exactly `exit`, the original parent must exit with status 0, without creating a child or printing another prompt.
Other commands still execute as before.

Build and submit with `/challenge/check shell`.
