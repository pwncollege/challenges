#define _GNU_SOURCE
#include <err.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/*
 * This level teaches gdb's `run` with stdin redirection, so debug-me only
 * cooperates when both hold:
 *   1. it is running under a debugger, and
 *   2. its standard input is the file /challenge/secret
 * i.e. you launched it with `(gdb) run < /challenge/secret`. NUM is baked in at
 * build time, so the only way to learn it is to satisfy both conditions and let
 * the program print it -- you can't just read it out of a file.
 */

static int being_traced(void)
{
    FILE *status = fopen("/proc/self/status", "r");
    if (!status)
        return 0;

    char line[256];
    int tracer = 0;
    while (fgets(line, sizeof line, status))
        if (sscanf(line, "TracerPid: %d", &tracer) == 1)
            break;

    fclose(status);
    return tracer != 0;
}

int main(void)
{
    if (!being_traced()) {
        puts("Run me under gdb for this challenge.");
        return 1;
    }

    char stdin_path[256];
    ssize_t len = readlink("/proc/self/fd/0", stdin_path, sizeof stdin_path - 1);
    if (len < 0)
        err(1, "readlink /proc/self/fd/0");
    stdin_path[len] = '\0';

    if (strcmp(stdin_path, "/challenge/secret") != 0) {
        puts("Redirect /challenge/secret into my stdin: (gdb) run < /challenge/secret");
        return 1;
    }

    /* Drain the redirected file so we genuinely consume the stdin we required. */
    char buf[256];
    while (read(0, buf, sizeof buf) > 0)
        continue;

    printf("secret number: %d\n", NUM);
    return 0;
}
