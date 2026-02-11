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
    puts("We write code in order to express an idea which can be reproduced and refined. We can think of our analysis as a program");
    puts("which injests the target to be analyzed as data. As the saying goes, code is data and data is code.\n");
    puts("While using gdb interactively as we've done with the past levels is incredibly powerful, another powerful tool is gdb");
    puts("scripting. By scripting gdb, you can very quickly create a custom-tailored program analysis tool. If you know how to");
    puts("interact with gdb, you already know how to write a gdb script--the syntax is exactly the same. You can write your");
    puts("commands to some file, for example `x.gdb`, and then launch gdb using the flag `-x <PATH_TO_SCRIPT>`. This file will");
    puts("execute all of the gdb commands after gdb launches. Alternatively, you can execute individual commands with `-ex");
    puts("'<COMMAND>'`. You can pass multiple commands with multiple `-ex` arguments. Finally, you can have some commands be");
    puts("always executed for any gdb session by putting them in `~/.gdbinit`. You probably want to put `set disassembly-flavor");
    puts("intel` in there.\n");
    puts("Within gdb scripting, a very powerful construct is breakpoint commands. Consider the following gdb script:\n");
    puts("  start");
    puts("  break *main+42");
    puts("  commands");
    puts("    x/gx $rbp-0x32");
    puts("    continue");
    puts("  end");
    puts("  continue");
    puts("");

    puts("In this case, whenever we hit the instruction at `main+42`, we will output a particular local variable and then continue");
    puts("execution.\n");
    puts("Now consider a similar, but slightly more advanced script using some commands you haven't yet seen:\n");
    puts("  start");
    puts("  break *main+42");
    puts("  commands");
    puts("    silent");
    puts("    set $local_variable = *(unsigned long long*)($rbp-0x32)");
    puts("    printf \"Current value: %llx\\n\", $local_variable");
    puts("    continue");
    puts("  end");
    puts("  continue");
    puts("");

    puts("In this case, the `silent` indicates that we want gdb to not report that we have hit a breakpoint, to make the output a");
    puts("bit cleaner. Then we use the `set` command to define a variable within our gdb session, whose value is our local");
    puts("variable. Finally, we output the current value using a formatted string.\n");
    puts("Use gdb scripting to help you collect the random values.\n");
    breakpoint();

    for (int i = 0; i < 8; i++)
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