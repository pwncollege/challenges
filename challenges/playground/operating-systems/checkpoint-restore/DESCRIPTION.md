A process has more state than its memory: the kernel also tracks its open files, permissions, working directory, and signal mask.
Implement two system calls that let a process save its state and return to it later:

```c
long checkpoint(void);
long restore(void);
```

`checkpoint()` saves the calling process's state and returns **0**.
`restore()` returns execution to that same point, making `checkpoint()` return **1** after the first restore, **2** after the second, and so on.
On success, execution never reaches the instruction after `restore()`.
Keep the same process, PID, and TGID; do not create or switch to another task.

Each process can keep one checkpoint and restore it repeatedly.
A new checkpoint replaces the old one and resets the generation to zero.
If saving a new checkpoint fails, keep the old one intact.

The saved state must include:

- Userspace memory, general-purpose registers, flags, and the instruction and stack pointers.
- Open file descriptors, descriptor flags, and offsets for ordinary seekable files.
  Descriptors created with `dup()` must still share an offset after restoring.
- The working directory, filesystem root, and umask.
- The blocked signal mask.
- User and group IDs, supplementary groups, and capabilities.
  A process that saves a checkpoint as root must be able to drop its privileges and regain them with `restore()`.

Use Linux's fork and copy-on-write machinery to save memory without copying every page yourself.
Keep an independent saved address space available after each restore.
Restore private memory, but leave shared mappings and external effects alone: file writes, pipe contents, network traffic, terminal output, child processes, and filesystem changes are not undone.

Support single-threaded x86-64 processes.
You do not need to restore floating-point/SIMD state or support changes to TLS or namespaces.
Assume other processes are not concurrently using the same open file descriptions.

Return `-ENOENT` from `restore()` when no checkpoint exists, and `-EOPNOTSUPP` from either syscall for a multithreaded caller.
Discard the checkpoint on successful `exec()` and on exit.
Children created by `fork()` start without a checkpoint.

Make your changes in `/usr/src/linux`, which contains the configured and built kernel source with no syscall changes applied.
Register `checkpoint` as syscall **470** and `restore` as **471** in `arch/x86/entry/syscalls/syscall_64.tbl`, and add their declarations to `include/linux/syscalls.h`.
The header `/challenge/checkpoint.h` lets C programs call them.
Read the ten programs in `/challenge/tests/` for examples of the expected behavior, then rebuild and test your kernel:

```console
hacker@dojo:~$ cd /usr/src/linux
hacker@dojo:/usr/src/linux$ make -j4
hacker@dojo:/usr/src/linux$ /challenge/run
```

`/challenge/run` boots your kernel in a virtual machine and runs all ten programs, reporting which pass and fail.
Pass the tests to get the flag!
