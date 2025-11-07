The first few challenges in this dojo will walk you through the creation of your first basic cIMG image.
Of course, the point of this is not to create images, but rather to experience the process of understanding a program, and by extension understanding logic and data formats used by the program, just from reversing its binary.

The `/challenge/cimg` binary in this level is (the start of) an image rendering program, specifically focusing on the cIMG format.
Software identifies the formats of files (e.g., whether the file is a GIF, a JPEG, an MP3, or so on) in a few ways:

1. The file extension.
   This is the part of the file after the `.`: a `ZardusSmiling.jpg` is probably a JPEG (image) of Zardus smiling, whereas `KanakLaughing.mp3` is probably an MP3 (audio) of Kanak laughing.
2. The _magic number_.
   Files can get renamed, or the filenames associated with files can be lost (e.g., in a partial filesystem failure) or simply missing (e.g., in a data stream).
   Thus, most file formats include a _magic number_ in the format that a parser can check to identify it.

You've already interacted with plenty of files containing magic numbers.
For example, the ELF binary files you've worked with all start with the bytes `\x7fELF`.
Of course, to you, this looks like a semantic-bearing string of characters, but a computer reads it as a number, hence the term.

In this challenge, you must craft a file with a `cimg` extension that contains the correct magic number.
You can learn this magic number by reversing the `/challenge/cimg` binary.
If you properly get past the magic number check, the challenge will give you the flag!

----

**Approach Suggestions:**
Some hopefully-useful suggestions to get you started:

- Reverse engineering can be done "statically" (e.g., in a graphical reversing tool such as IDA and the like, with the program you are trying to understand remaining "at rest") or "dynamically" (e.g., in a debugger such as gdb, with the program you are trying to understand running).
  We recommend a combination of these techniques throughout this module.
  Use your graphical reversing tool to form hypotheses about the program (e.g., "it compares some bytes of my input against something at this assembly instruction address") and then verify these hypotheses in gdb (e.g., break at the address in question, look at the values of the registers it compares, and correlate them with your input).
- **Leave objdump behind.** You might have used objdump previously to look at assembly code.
  You might be able to solve this level (and maybe the next) with objdump, but **you cannot do this module** without a good graphical reversing tool.
  Use this challenge as impetus to begin gaining familiarity with a graphical reversing tool.
- Retrace your successful solution.
  If you solve this challenge without using _both_ a graphical reversing tool and a debugger (gdb), go back and re-verify your solution using the tools that you did not use.
  This will be good practice for understanding how to use these tools in later levels, and you should apply it in any challenge that you solve without relying on both tools.
