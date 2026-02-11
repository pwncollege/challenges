#define _GNU_SOURCE 1

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/signal.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/sendfile.h>
#include <sys/prctl.h>
#include <sys/personality.h>
#include <arpa/inet.h>

void __attribute__((constructor)) auto_gdb(int argc, char **argv, char **envp)
{
    char program_path[256] = { 0 };
    char parent_path_symlink[256] = { 0 };
    char parent_path[256] = { 0 };
    char *gdb_argv[256] = { 0 };
    int i;

    snprintf(parent_path_symlink, sizeof(parent_path_symlink), "/proc/%d/exe", getppid());
    readlink(parent_path_symlink, parent_path, sizeof(program_path) - 1);

    if (!strcmp(parent_path, "/usr/bin/gdb"))
        return;

    readlink("/proc/self/exe", program_path, sizeof(program_path) - 1);

    gdb_argv[0] = "/usr/bin/gdb";
    assert(argc < 250);
    for (i = 1; i < argc; i++)
        gdb_argv[i] = argv[i];
    gdb_argv[i++] = "--args";
    gdb_argv[i++] = program_path;
    gdb_argv[i++] = NULL;

    puts("The program is restarting under the control of gdb! You can run the program with the gdb command `run`.\n");
    execve(gdb_argv[0], gdb_argv, envp);
}

void win()
{
    static char flag[256];
    static int flag_fd;
    static int flag_length;

    puts("You win! Here is your flag:");
    flag_fd = open("/flag", 0);
    if (flag_fd < 0)
    {
        printf("\n  ERROR: Failed to open the flag -- %s!\n", strerror(errno));
        if (geteuid() != 0)
        {
            printf("  Your effective user id is not 0!\n");
            printf("  You must directly run the suid binary in order to have the correct permissions!\n");
        }
        exit(-1);
    }
    flag_length = read(flag_fd, flag, sizeof(flag));
    if (flag_length <= 0)
    {
        printf("\n  ERROR: Failed to read the flag -- %s!\n", strerror(errno));
        exit(-1);
    }
    write(1, flag, flag_length);
    printf("\n\n");
}

void __attribute__((always_inline)) breakpoint()
{
    __asm__ volatile("int3");
}

int main(int argc, char **argv, char **envp)
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("###\n");
    printf("### Welcome to %s!\n", argv[0]);
    printf("###\n");
    printf("\n");

    puts("GDB is a very powerful dynamic analysis tool which you can use in order to understand the state of a program throughout");
    puts("its execution. You will become familiar with some of gdb's capabilities in this module.\n");
    puts("You can examine the contents of memory using the `x/<n><u><f> <address>` parameterized command. In this format `<u>` is");
    puts("the unit size to display, `<f>` is the format to display it in, and `<n>` is the number of elements to display. Valid");
    puts("unit sizes are `b` (1 byte), `h` (2 bytes), `w` (4 bytes), and `g` (8 bytes). Valid formats are `d` (decimal), `x`");
    puts("(hexadecimal), `s` (string) and `i` (instruction). The address can be specified using a register name, symbol name, or");
    puts("absolute address. Additionally, you can supply mathematical expressions when specifying the address.\n");
    puts("For example, `x/8i $rip` will print the next 8 instructions from the current instruction pointer. `x/16i main` will");
    puts("print the first 16 instructions of main. You can also use `disassemble main`, or `disas main` for short, to print all of");
    puts("the instructions of main. Alternatively, `x/16gx $rsp` will print the first 16 values on the stack. `x/gx $rbp-0x32`");
    puts("will print the local variable stored there on the stack.\n");
    puts("You will probably want to view your instructions using the CORRECT assembly syntax. You can do that with the command");
    puts("`set disassembly-flavor intel`.\n");
    puts("In order to solve this level, you must figure out the random value on the stack (the value read in from `/dev/urandom`).");
    puts("Think about what the arguments to the read system call are.\n");
    breakpoint();

    for (int i = 0; i < 1; i++)
    {
        uint64_t correct;
        uint64_t input;
        read(open("/dev/urandom", 0), &correct, sizeof(correct));

        puts("The random value has been set!\n");

        breakpoint();

        printf("Random value: ");
        scanf("%llx", &input);

        printf("You input: %llx\n", input);
        printf("The correct answer is: %llx\n", correct);

        if (input != correct)
            exit(1);
    }

    win();

    printf("### Goodbye!\n");
}