In the previous challenge, you changed the kernel and rebuilt it.
Linux can also load code into a running kernel through a **kernel module**.
A module can register a device whose file operations run kernel code when a program reads or writes a path in `/dev`.

Read the module source in `/challenge/flag.c`, then run `/challenge/run` to enter a virtual machine with a root shell.
The compiled module is installed in the virtual machine's `/lib/modules/$(uname -r)/updates/` directory.
Use `modprobe flag` inside the virtual machine to load it by name, then investigate the `/dev/flag` device it creates.
Use `lsmod` to list the loaded modules and confirm that `flag` is loaded.

Read the source to work out how to get the flag from the device.
You can use `modprobe -r flag` to unload the module and load it again to reset its state.
Exit the shell to shut down the virtual machine.
