#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/personality.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

extern char **environ;

#define FLAG_FD       100
#define MY_SENT_FD    101
#define OTHER_SENT_FD 102

static const char *SHELL_SENTINEL = "/challenge/.shell-sentinel";
static const char *GDB_SENTINEL   = "/challenge/.gdb-sentinel";

static int looks_like_post_exec(void)
{
    struct stat st;
    return fstat(FLAG_FD, &st) == 0;
}

static int is_traced(void)
{
    int fd = open("/proc/self/status", O_RDONLY);
    if (fd < 0)
        return 0;
    char buf[4096];
    ssize_t n = read(fd, buf, sizeof buf - 1);
    close(fd);
    if (n <= 0)
        return 0;
    buf[n] = 0;
    char *p = strstr(buf, "TracerPid:");
    if (!p)
        return 0;
    return atoi(p + sizeof("TracerPid:") - 1) != 0;
}

static int read_flag_into_memfd(void)
{
    int file = open("/flag", O_RDONLY);
    if (file < 0) {
        perror("open /flag");
        return -1;
    }
    int memfd = syscall(SYS_memfd_create, "f", 0);
    if (memfd < 0) {
        perror("memfd_create flag");
        close(file);
        return -1;
    }
    char buf[256];
    ssize_t n;
    while ((n = read(file, buf, sizeof buf)) > 0) {
        if (write(memfd, buf, n) != n) {
            perror("write flag");
            close(file);
            close(memfd);
            return -1;
        }
    }
    close(file);
    lseek(memfd, 0, SEEK_SET);
    if (dup2(memfd, FLAG_FD) < 0) {
        perror("dup2");
        close(memfd);
        return -1;
    }
    close(memfd);
    return 0;
}

static int open_sentinels(int traced)
{
    const char *my_path    = traced ? GDB_SENTINEL   : SHELL_SENTINEL;
    const char *other_path = traced ? SHELL_SENTINEL : GDB_SENTINEL;

    int my = open(my_path, O_WRONLY | O_APPEND);
    if (my < 0) {
        perror(my_path);
        return -1;
    }
    if (dup2(my, MY_SENT_FD) < 0) {
        perror("dup2 my sentinel");
        close(my);
        return -1;
    }
    close(my);

    int other = open(other_path, O_RDONLY);
    if (other < 0) {
        perror(other_path);
        return -1;
    }
    if (dup2(other, OTHER_SENT_FD) < 0) {
        perror("dup2 other sentinel");
        close(other);
        return -1;
    }
    close(other);
    return 0;
}

static int copy_self_to_memfd(void)
{
    int self = open("/proc/self/exe", O_RDONLY);
    if (self < 0) {
        perror("open /proc/self/exe");
        return -1;
    }
    int memfd = syscall(SYS_memfd_create, "p", 0);
    if (memfd < 0) {
        perror("memfd_create exe");
        close(self);
        return -1;
    }
    char buf[8192];
    ssize_t n;
    while ((n = read(self, buf, sizeof buf)) > 0) {
        if (write(memfd, buf, n) != n) {
            perror("write self");
            close(self);
            close(memfd);
            return -1;
        }
    }
    close(self);
    return memfd;
}

static int do_setup_phase(int argc, char **argv)
{
    /* All the privileged file work happens here, before we drop privs:
     * - read /flag into a memfd (FD 100)
     * - open my-context sentinel for write (FD 101)
     * - open other-context sentinel for read (FD 102)
     * The kernel checks open() permissions at open time, so the resulting
     * FDs keep their access rights even after we drop privs and re-exec. */
    if (read_flag_into_memfd() < 0)
        return 1;
    if (open_sentinels(is_traced()) < 0)
        return 1;

    int pers = personality(0xFFFFFFFF);
    if (personality(pers | ADDR_NO_RANDOMIZE) == -1) {
        perror("personality");
        return 1;
    }

    if (setresuid(getuid(), getuid(), getuid()) < 0) {
        perror("setresuid");
        return 1;
    }

    int exe_memfd = copy_self_to_memfd();
    if (exe_memfd < 0)
        return 1;
    char path[64];
    snprintf(path, sizeof path, "/proc/self/fd/%d", exe_memfd);
    execve(path, argv, environ);
    perror("execve");
    return 1;
}

static int do_challenge_phase(int argc, char **argv)
{
    if (argc != 1) {
        fprintf(stderr,
                "argc == %d, but I need argc == 1. Run me with no extra arguments.\n",
                argc);
        return 1;
    }

    unsigned long a0 = (unsigned long)argv[0];
    if ((a0 & 0xFFFF) != 0x5390) {
        fprintf(stderr,
                "argv[0] = %p; I need (argv[0] & 0xFFFF) == 0x5390.\n"
                "Tune the length of an environment variable to shift it.\n",
                argv[0]);
        return 1;
    }

    /* Mark this context as solved (writes to a root-owned sentinel via the
     * pre-drop FD; the user can't fake this). */
    if (write(MY_SENT_FD, "1", 1) != 1) {
        perror("write sentinel");
        return 1;
    }
    fsync(MY_SENT_FD);
    close(MY_SENT_FD);

    /* Check whether the other context has been solved too. */
    char marker[1];
    ssize_t got = read(OTHER_SENT_FD, marker, 1);
    close(OTHER_SENT_FD);

    if (got == 1) {
        /* Both contexts done -- print the flag. */
        char buf[256];
        ssize_t n = read(FLAG_FD, buf, sizeof buf);
        if (n > 0)
            write(1, buf, n);
        close(FLAG_FD);
        return 0;
    }

    int traced = is_traced();
    fprintf(stderr,
            "argv[0] aligned in the %s context. "
            "Now align it %s to unlock the flag.\n",
            traced ? "GDB" : "shell",
            traced ? "from a shell (`env -i FOO=... /challenge/program`)"
                   : "under GDB (`gdb /challenge/program`, then "
                     "`set exec-wrapper env -i FOO=...; run`)");
    return 1;
}

int main(int argc, char **argv)
{
    if (looks_like_post_exec())
        return do_challenge_phase(argc, argv);
    return do_setup_phase(argc, argv);
}
