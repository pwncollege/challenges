Support for different directives allow fairly advanced cIMG functionality.
For example, you previously created the images you needed by specifying all of the pixels explicitly.
However, with the advanced functionality added in this level, that is no longer necessary!
Consequently, the challenge will not give you the flag if you use too many bytes to make the right image.
Good luck.

----
**Approach Suggestion:**
This level will require you to create a cimage with multiple directives in one file.
Some hopefully-useful suggestions:

- Your first several attempts at this will likely result in an error message.
  **Do not simply guess at how to fix this error message!**
  Instead, use a combination of a graphical reversing tool and a debugger (gdb) to actually understand which check is failing, and adjust your input to avoid failing this check.
- Writing your cimage by hand will be very error-prone.
  Consider creating a Python script to generate cimages.
  Your script should somewhat mirror the parser library, with a function to generate the cimage header and functions for every directive that you want to support.
  This will make your life MUCH easier in this and future levels.
