You've learned to read and write registers, walk through memory, and package your code as a function inside a shared library.
Now let's put those skills together and build a calculator.
When you need to debug one of these `.so` submissions, refer back to [Writing from a Shared Library](/computing-101/control-flow/callee-write) for the shared-library debugging pattern.

The calculator's operands arrive as text, but arithmetic instructions work on numbers.
We'll build functions to convert in both directions, then use them to read an expression, compute its result, and print the answer.
Keep your solutions as you go: the calculator will use the functions you write along the way.
