Computers run _computer programs_ to achieve different goals.
One program might be your favorite video game, another is the web browser you're using to access this website, and so on.

A program is made of _computer code_, and this code is made of a huge amount of individual _instructions_ that cause the computer to carry out computation and take certain actions based on the results.
Each individual instruction is typically very simple, and only in aggregate do they enable awesome things like letting you look at memes on the internet.

This computation is done by the _Central Processing Unit_ (CPU), in tandem with other pieces of hardware inside your computer.
Instructions are specified to the CPU in something called _Assembly Language_, and each CPU architecture uses a different flavor of this language.
Any program, no matter what language it is originally written in (e.g., C, C++, Java, Python, etc.), is eventually converted to or interpreted by Assembly instructions.

Most of pwn.college's material uses the [x86 CPU architecture](https://en.wikipedia.org/wiki/X86), which is Zardus' favorite architecture.
x86 was created by Intel in the dawn of the PC age, and has continued to evolve over the years.
Together, x86 and ARM (a different, less cool architecture) make up the majority of PC CPUs out there.

In this module, we will start out with the simplest x86 program that we can imagine, which we will write in x86 assembly, and build up from there!
Let's dig in, and write your first program!
