Your first task is to create the simplest possible program—one that immediately terminates when run.
In this challenge, you will use the [exit](https://man7.org/linux/man-pages/man2/_exit.2.html) syscall, which is responsible for ending a process and returning an exit status to the operating system.
This syscall takes a single argument: the exit status (with `0` typically indicating success).
Understanding how to cleanly exit a program is crucial because it ensures your process communicates its completion state properly.
