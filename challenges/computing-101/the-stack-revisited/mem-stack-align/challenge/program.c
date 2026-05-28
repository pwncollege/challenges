/* Two-phase trick to keep the user-facing "just run /challenge/program" UX:
 *
 *   1. SUID phase opens /flag (stashed as FD 100, inherited across execve),
 *      sets ADDR_NO_RANDOMIZE for the next exec, drops privileges, and
 *      re-execs a non-SUID memfd copy of itself.
 *   2. The re-exec'd phase has deterministic addresses (no ASLR) and a clean
 *      FD 100 it can read the flag from. argv[0]'s low bits are now a pure
 *      function of env-string lengths -- which is the lesson.
 *
 * Why memfd-copy for the re-exec? Re-execing the SUID binary triggers
 * secureexec and clears ADDR_NO_RANDOMIZE. A memfd carries no SUID bit.
 */

#define _GNU_SOURCE
#include <err.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/personality.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

extern char **environ;

#define FLAG_FD 100

static int re_exec_phase(void) {
    struct stat st;
    return fstat(FLAG_FD, &st) == 0;
}

static void inherit_fd(const char *path, int target, int flags) {
    int fd = open(path, flags);
    if (fd < 0) err(1, "open %s", path);
    if (dup2(fd, target) < 0) err(1, "dup2 %s", path);
    close(fd);
}

static int memfd_clone(const char *path) {
    int src = open(path, O_RDONLY);
    if (src < 0) err(1, "open %s", path);
    int dst = syscall(SYS_memfd_create, "clone", 0);
    if (dst < 0) err(1, "memfd_create");
    char buf[8192];
    ssize_t n;
    while ((n = read(src, buf, sizeof buf)) > 0)
        if (write(dst, buf, n) != n) err(1, "write");
    close(src);
    return dst;
}

static void setup_phase(char **argv) {
    inherit_fd("/flag", FLAG_FD, O_RDONLY);

    if (personality(personality(0xFFFFFFFF) | ADDR_NO_RANDOMIZE) < 0)
        err(1, "personality");
    if (setresuid(getuid(), getuid(), getuid()) < 0)
        err(1, "setresuid");

    int exe = memfd_clone("/proc/self/exe");
    char path[64];
    snprintf(path, sizeof path, "/proc/self/fd/%d", exe);
    execve(path, argv, environ);
    err(1, "execve");
}

static int challenge_phase(int argc, char **argv) {
    if (argc != 1) {
        fprintf(stderr, "argc == %d, but I need argc == 1.\n", argc);
        return 1;
    }
    if (((unsigned long)argv[0] & 0xFFFF) != 0x5390) {
        fprintf(stderr,
                "argv[0] = %p; I need (argv[0] & 0xFFFF) == 0x5390.\n"
                "Tune the length of an environment variable to shift it.\n",
                argv[0]);
        return 1;
    }

    char buf[256];
    ssize_t n = read(FLAG_FD, buf, sizeof buf);
    if (n > 0) write(1, buf, n);
    return 0;
}

int main(int argc, char **argv) {
    if (re_exec_phase()) return challenge_phase(argc, argv);
    setup_phase(argv);
    return 1; /* unreachable */
}
