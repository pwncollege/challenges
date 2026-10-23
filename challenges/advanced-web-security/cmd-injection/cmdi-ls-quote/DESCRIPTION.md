An interesting thing about command injection is that you don't get to choose where in the command the injection occurs: the developer accidentally makes that choice for you when writing the program.
Sometimes, these injections occur in uncomfortable places.
Consider the following:

```python
os.system(f"echo Hello '{word}'")
```

Here, the developer tried to convey to the shell that `word` should really be only one word.
The shell, when given arguments in single quotes, treats otherwise-special characters like `;`, `$`, and so on as just normal characters, until it hits the closing single quote (`'`).

This level gives you this scenario.
Can you bypass it?

----
**HINT:**
Keep in mind that there will be a `'` character right at the end of whatever you inject.
In the shell, all quotes must be matched with a partner, or the command is invalid.
Make sure to craft your injection so that the resulting command is valid!
