/* See ../../../the-stack/mem-stack-align/challenge/program.c for the SUID +
 * memfd re-exec rationale (deterministic argv[0] without a privileged
 * container) and for the per-instance target-file idea.
 *
 * The added wrinkle here: the binary must be solved twice -- once from a
 * shell, once under GDB -- to make "GDB shapes the inferior's stack
 * differently" concrete. We keep two pieces of state per context: a
 * sentinel (proof the user hit the target there) and a target file
 * (chosen on the first run in that context, BYTES_DELTA below the
 * baseline argv[0]). All four files are root-owned mode-600; the program
 * only touches them via FDs inherited across the post-privilege-drop
 * execve.
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

#define FLAG_FD            100
#define MY_SENT_FD         101
#define OTHER_SENT_FD      102
#define MY_TARGET_FD       103

#define SHELL_SENTINEL "/challenge/.shell-sentinel"
#define GDB_SENTINEL   "/challenge/.gdb-sentinel"
#define SHELL_TARGET   "/challenge/.shell-target"
#define GDB_TARGET     "/challenge/.gdb-target"

#define BYTES_DELTA 0x80   /* same as mem-stack-align; small enough to type */

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
    int traced = is_traced();
    inherit_fd("/flag", FLAG_FD, O_RDONLY);
    inherit_fd(traced ? GDB_SENTINEL : SHELL_SENTINEL, MY_SENT_FD,    O_WRONLY | O_APPEND);
    inherit_fd(traced ? SHELL_SENTINEL : GDB_SENTINEL, OTHER_SENT_FD, O_RDONLY);
    inherit_fd_create(traced ? GDB_TARGET : SHELL_TARGET, MY_TARGET_FD, O_RDWR | O_CREAT);

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
    if (lseek(MY_TARGET_FD, 0, SEEK_SET) < 0) return 0;
    ssize_t n = read(MY_TARGET_FD, buf, sizeof buf - 1);
    if (n <= 0) return 0;
    buf[n] = 0;
    return strtoul(buf, NULL, 0);
}

static void write_persisted_target(unsigned long target) {
    char buf[32];
    int len = snprintf(buf, sizeof buf, "0x%lx", target);
    if (ftruncate(MY_TARGET_FD, 0) < 0) err(1, "ftruncate target");
    if (pwrite(MY_TARGET_FD, buf, len, 0) != len) err(1, "pwrite target");
    fsync(MY_TARGET_FD);
}

static int challenge_phase(int argc, char **argv) {
    if (argc != 1) {
        fprintf(stderr, "argc == %d, but I need argc == 1.\n", argc);
        return 1;
    }

    int traced = is_traced();
    const char *ctx = traced ? "GDB" : "shell";
    unsigned long current = (unsigned long)argv[0] & 0xFFFF;
    unsigned long target = read_persisted_target();

    if (target == 0) {
        target = (current - BYTES_DELTA) & 0xFFFF;
        write_persisted_target(target);
        fprintf(stderr,
                "argv[0] = %p; first run in the %s context. I'm picking your target:\n"
                "  (argv[0] & 0xFFFF) == 0x%lx --- %d bytes below the current value.\n"
                "Tune an environment variable to shift argv[0] there%s.\n",
                argv[0], ctx, target, BYTES_DELTA,
                traced ? " (use `set exec-wrapper env -i FOO=...; run`)"
                       : " (use `env -i FOO=... /challenge/program`)");
        return 1;
    }

    if (current != target) {
        long delta = (long)((current - target) & 0xFFFF);
        fprintf(stderr,
                "argv[0] = %p; in the %s context I need (argv[0] & 0xFFFF) == 0x%lx --- %ld bytes below the current value.\n"
                "Adjust your env padding to shift argv[0] there.\n",
                argv[0], ctx, target, delta);
        return 1;
    }

    if (write(MY_SENT_FD, "1", 1) != 1) err(1, "write sentinel");
    fsync(MY_SENT_FD);

    char marker;
    int other_done = (read(OTHER_SENT_FD, &marker, 1) == 1);
    if (other_done) {
        char buf[256];
        ssize_t n = read(FLAG_FD, buf, sizeof buf);
        if (n > 0) write(1, buf, n);
        return 0;
    }

    fprintf(stderr,
            "argv[0] aligned in the %s context. Now align it %s to unlock the flag.\n",
            ctx,
            traced ? "from a shell (`env -i FOO=... /challenge/program`)"
                   : "under GDB (`gdb /challenge/program`, then "
                     "`set exec-wrapper env -i FOO=...; run`)");
    return 1;
}

int main(int argc, char **argv) {
    if (re_exec_phase()) return challenge_phase(argc, argv);
    setup_phase(argv);
    return 1; /* unreachable */
}
