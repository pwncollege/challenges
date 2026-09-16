System calls let a program ask the kernel to do work on its behalf.
Here, you will implement the kernel side of that interface.

The Linux 6.18.52 source is in `/usr/src/linux`, configured and built for a small virtual machine.
We've registered system call **470** as `hello` and provided a stub that returns `-ENOSYS` ("Function not implemented").
Run `git diff` in the source directory to see how it's connected:

```console
hacker@dojo:~$ cd /usr/src/linux
hacker@dojo:/usr/src/linux$ git diff
```

- `arch/x86/entry/syscalls/syscall_64.tbl`: registers system calls and their numbers on x86-64.
- `include/linux/syscalls.h`: declares system call functions.
- `kernel/sys.c`: contains the `hello` stub you'll implement.

Make your edits in `/usr/src/linux/kernel/sys.c`, replacing the body of `SYSCALL_DEFINE1(hello, ...)`.
The `name` argument is a pointer to a null-terminated string in userspace.
Write `Hello, <name>!` to the kernel log, replacing `<name>` with that string.
For example, passing `Alice` should produce `Hello, Alice!`.
Copy the string safely from userspace before using it in the kernel.

Rebuild your changes, then use `/challenge/run` to test your kernel:

```console
hacker@dojo:/usr/src/linux$ make -j4
hacker@dojo:/usr/src/linux$ /challenge/run
```

`/challenge/run` boots your kernel in a virtual machine and calls your syscall with several names.
Print each greeting correctly to get the flag!
You can use `git diff` in the source tree to review your changes.
