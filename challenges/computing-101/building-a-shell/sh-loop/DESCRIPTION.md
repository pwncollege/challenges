Your parent can now wait for a command to finish.
Instead of exiting afterward, let it accept another command.

Put the prompt, input, child creation, and wait into a loop in the original parent.
Print `$ ` before each input, and remove the final message from the previous level.
Each child executes one command.
When `read` returns zero, there is no more input: end the parent with status 0.
Let your input routine report that condition to the loop, or call `read` yourself and pass its input to your `sscanf`.

The checker supplies one complete command per `read`, within the same 255-byte limit.
The commands may themselves return a nonzero status; the parent still continues.

Run a few commands in your shell, then submit it with `/challenge/check shell`.
