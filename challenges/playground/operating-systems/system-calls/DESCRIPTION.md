System calls let a program ask the kernel to do work on its behalf.
Here, you will implement the kernel side of that interface.

The Linux 6.18.52 source is in `/usr/src/linux`, configured and built for a small virtual machine.
Add a system call named `hello` at number **470** in the native x86-64 syscall table.
It should accept a pointer to a null-terminated string in userspace and write `Hello, <name>!` to the kernel log, replacing `<name>` with that string.
For example, passing `Alice` should produce `Hello, Alice!`.
Copy the string safely from userspace before using it in the kernel.

Build your changes and run the grader:

```console
hacker@dojo:~$ cd /usr/src/linux
hacker@dojo:/usr/src/linux$ make -j4
hacker@dojo:/usr/src/linux$ /challenge/run
```

The grader boots your kernel and calls your syscall with several names.
Print each greeting correctly to get the flag!
You can use `git diff` in the source tree to review your changes.
