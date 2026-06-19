Programs keep extensive internal state about the actions they have taken or should take in the future.
This version of `/challenge/cimg` tracks much more state than before, which allows it to impose strict requirements on your input before it gives you the flag.
Figure out what image it wants, and score!

----
**Approach Suggestion:**
This challenge processes and displays your input like before, and in the process maintains an expected state to check.
To understand what your input should be, you might consider the following approach typical of a Reverse Engineering pipeline:

1. Understand what the program expects its internal state to be to give you the flag.
   You should do this using a combination of an graphical reversing tool (IDA, etc) to form hypotheses about what the program is doing to your input and a runtime debugger (gdb) to verify those hypotheses at runtime.
   For example, at some specific assembly instruction, the program makes a decision about whether or not to give you the flag.
   Find this point in your graphical reversing tool, then verify your understanding at runtime with gdb.
   Strive to understand what the data that it is checking agianst _means_, at least on a high level.
   A check is typically done between some questionable data (in this case, some transformation of your image) and known-good data.
   What is the latter in this scenario?
2. Understand how the program uses your input to generate the "questionable" data that it checks in its decision making process.
   Programs implement algorithms, and these algorithms can be understood.
   What's the algorithm that transforms your input into the data used by the program to make decisions?
   Can you verify this hypothesis with gdb?
   Can you use this verified knowledge to tweak your input to change the program's behavior just a bit (e.g., get a bit further before the program decides you don't get the flag)?
3. Many algorithms that transform data from `A` (in this case, your input data) to `B` (in this case, the "questionable" data that is compared against the known-good data) can be inverted to create an algorithm that transforms `B` back to `A`.
   Can you use the knowledge derived from step 2 to create such an algorithm?
   In other words, can you create an algorithm to translate from the internal state of the program back to your input data?
   First, manually apply it to some data to see if it makes a difference to how the program treats your input.
4. Now you have an algorithm that can take the program's expected state and produce input data that will cause the program to reach that internal state.
   Next, you need to extract the "known-good" internal state that the program expects.
   This can be done in many ways, but the two go-tos are your graphical reversing tool and your debugger (gdb): both can accomplish the task of extracting the expected state to a file.
5. Apply your algorithm from Step 3 to the extracted known-good state in Step 4 to get an input that should trigger the expected state.
   Plop the right metadata on it (whatever magic numbers and so on that the program needs) and feed it into the program!
