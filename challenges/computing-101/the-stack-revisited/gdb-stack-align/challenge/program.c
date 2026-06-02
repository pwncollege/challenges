/* See ../../../the-stack/mem-stack-align/challenge/program.c for the SUID +
 * memfd re-exec rationale (deterministic argv[0] without a privileged
 * container).
 *
 * The lesson: gdb passes its own environment (a few variables beyond what
 * the bare shell has) to the inferior, so a program's argv[0] lands at a
 * different address under gdb than it does from a bare shell. To make the
 * shift concrete we have the learner:
 *
 *   1. Run /challenge/program under gdb --- the program captures its own
 *      argv[0] and persists it as the target.
 *   2. Quit gdb. Run /challenge/program from the shell, padding the regular
 *      shell environment (just `FOO=xxx /challenge/program` --- no env -i)
 *      until the shell's argv[0] lands at the saved target.
 *
 * The target file is root-owned mode-600 and inherited as FD 103 across
 * the privilege-drop execve. If the learner runs us from the shell before
 * running under gdb at least once, we bail and tell them to start with
 * gdb.
 */

#define _GNU_SOURCE
#include <err.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/personality.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

extern char **environ;

#define FLAG_FD     100
#define TARGET_FD   103
#define TARGET_PATH "/challenge/.target"

static int re_exec_phase(void) {
    struct stat st;
    return fstat(FLAG_FD, &st) == 0;
}

static int is_traced(void) {
    int fd = open("/proc/self/status", O_RDONLY);
    if (fd < 0) return 0;
    char buf[4096];
    ssize_t n = read(fd, buf, sizeof buf - 1);
    close(fd);
    if (n <= 0) return 0;
    buf[n] = 0;
    char *p = strstr(buf, "TracerPid:");
    return p && atoi(p + sizeof("TracerPid:") - 1) != 0;
}

static void inherit_fd(const char *path, int target, int flags) {
    int fd = open(path, flags);
    if (fd < 0) err(1, "open %s", path);
    if (dup2(fd, target) < 0) err(1, "dup2 %s", path);
    close(fd);
}

static void inherit_fd_create(const char *path, int target, int flags) {
    int fd = open(path, flags, 0600);
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
    inherit_fd_create(TARGET_PATH, TARGET_FD, O_RDWR | O_CREAT);

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

static unsigned long read_persisted_target(void) {
    char buf[32];
    if (lseek(TARGET_FD, 0, SEEK_SET) < 0) return 0;
    ssize_t n = read(TARGET_FD, buf, sizeof buf - 1);
    if (n <= 0) return 0;
    buf[n] = 0;
    return strtoul(buf, NULL, 0);
}

static void write_persisted_target(unsigned long target) {
    char buf[32];
    int len = snprintf(buf, sizeof buf, "0x%lx", target);
    if (ftruncate(TARGET_FD, 0) < 0) err(1, "ftruncate target");
    if (pwrite(TARGET_FD, buf, len, 0) != len) err(1, "pwrite target");
    fsync(TARGET_FD);
}

static int challenge_phase(int argc, char **argv) {
    if (argc != 1) {
        fprintf(stderr, "argc == %d, but I need argc == 1.\n", argc);
        return 1;
    }

    int traced = is_traced();
    unsigned long current = (unsigned long)argv[0];

    if (traced) {
        write_persisted_target(current);
        fprintf(stderr,
                "argv[0] is at 0x%lx (running under GDB) --- saved as your target.\n"
                "Quit gdb, then run `/challenge/program` from your shell with environment\n"
                "padding (`FOO=xxxxxxxx /challenge/program`) until argv[0] lands here.\n",
                current);
        return 1;
    }

    unsigned long target = read_persisted_target();
    if (target == 0) {
        fprintf(stderr,
                "argv[0] is at 0x%lx (running in the shell), but I don't have a target yet.\n"
                "Run me under gdb first (`gdb /challenge/program`, then `run`) so I can\n"
                "capture the gdb-context argv[0].\n",
                current);
        return 1;
    }

    if (current != target) {
        long delta = (long)(current - target);
        if (delta > 0) {
            fprintf(stderr,
                    "argv[0] is at 0x%lx (running in the shell); I want it at 0x%lx "
                    "(where gdb put it).\nThat's %ld bytes lower --- pad your shell "
                    "environment to shift it there.\n",
                    current, target, delta);
        } else {
            fprintf(stderr,
                    "argv[0] is at 0x%lx (running in the shell); I want it at 0x%lx "
                    "(where gdb put it).\nThat's %ld bytes higher --- you've overshot. "
                    "Reduce your env padding.\n",
                    current, target, -delta);
        }
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
