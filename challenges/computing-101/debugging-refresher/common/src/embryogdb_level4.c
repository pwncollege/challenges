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
    puts("A critical part of dynamic analysis is getting your program to the state you are interested in analyzing. So far, these");
    puts("challenges have automatically set breakpoints for you to pause execution at states you may be interested in analyzing.");
    puts("It is important to be able to do this yourself.\n");
    puts("There are a number of ways to move forward in the program's execution. You can use the `stepi <n>` command, or `si <n>`");
    puts("for short, in order to step forward one instruction. You can use the `nexti <n>` command, or `ni <n>` for short, in");
    puts("order to step forward one instruction, while stepping over any function calls. The `<n>` parameter is optional, but");
    puts("allows you to perform multiple steps at once. You can use the `finish` command in order to finish the currently");
    puts("executing function. You can use the `break *<address>` parameterized command in order to set a breakpoint at the");
    puts("specified-address. You have already used the `continue` command, which will continue execution until the program hits a");
    puts("breakpoint.\n");
    puts("While stepping through a program, you may find it useful to have some values displayed to you at all times. There are");
    puts("multiple ways to do this. The simplest way is to use the `display/<n><u><f>` parameterized command, which follows");
    puts("exactly the same format as the `x/<n><u><f>` parameterized command. For example, `display/8i $rip` will always show you");
    puts("the next 8 instructions. On the other hand, `display/4gx $rsp` will always show you the first 4 values on the stack.");
    puts("Another option is to use the `layout regs` command. This will put gdb into its TUI mode and show you the contents of all");
    puts("of the registers, as well as nearby instructions.\n");
    puts("In order to solve this level, you must figure out a series of random values which will be placed on the stack. You are");
    puts("highly encouraged to try using combinations of `stepi`, `nexti`, `break`, `continue`, and `finish` to make sure you have");
    puts("a good internal understanding of these commands. The commands are all absolutely critical to navigating a program's");
    puts("execution.\n");
    breakpoint();

    for (int i = 0; i < 4; i++)
    {
        uint64_t correct;
        uint64_t input;
        read(open("/dev/urandom", 0), &correct, sizeof(correct));

        puts("The random value has been set!\n");

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