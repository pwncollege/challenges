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
    puts("As it turns out, gdb has FULL control over the target process. Not only can you analyze the program's state, but you can");
    puts("also modify it. While gdb probably isn't the best tool for doing long term maintenance on a program, sometimes it can be");
    puts("useful to quickly modify the behavior of your target process in order to more easily analyze it.\n");
    puts("You can modify the state of your target program with the `set` command. For example, you can use `set $rdi = 0` to zero");
    puts("out $rdi. You can use `set *((uint64_t *) $rsp) = 0x1234` to set the first value on the stack to 0x1234. You can use");
    puts("`set *((uint16_t *) 0x31337000) = 0x1337` to set 2 bytes at 0x31337000 to 0x1337.\n");
    puts("Suppose your target is some networked application which reads from some socket on fd 42. Maybe it would be easier for");
    puts("the purposes of your analysis if the target instead read from stdin. You could achieve something like that with the");
    puts("following gdb script:\n");
    puts("  start");
    puts("  catch syscall read");
    puts("  commands");
    puts("    silent");
    puts("    if ($rdi == 42)");
    puts("      set $rdi = 0");
    puts("    end");
    puts("    continue");
    puts("  end");
    puts("  continue");
    puts("");

    puts("This example gdb script demonstrates how you can automatically break on system calls, and how you can use conditions");
    puts("within your commands to conditionally perform gdb commands.\n");
    puts("In the previous level, your gdb scripting solution likely still required you to copy and paste your solutions. This");
    puts("time, try to write a script that doesn't require you to ever talk to the program, and instead automatically solves each");
    puts("challenge by correctly modifying registers / memory.\n");
    breakpoint();

    for (int i = 0; i < 64; i++)
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