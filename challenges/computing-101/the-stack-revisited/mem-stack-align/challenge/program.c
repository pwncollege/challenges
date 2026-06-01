/* Two-phase trick to keep the user-facing "just run /challenge/program" UX:
 *
 *   1. SUID phase opens /flag (stashed as FD 100, inherited across execve),
 *      opens a target file at FD 103 (created if missing), sets
 *      ADDR_NO_RANDOMIZE for the next exec, drops privileges, and re-execs
 *      a non-SUID memfd copy of itself.
 *   2. The re-exec'd phase has deterministic addresses (no ASLR) and clean
 *      FDs it can read/write. argv[0]'s low bits are now a pure function of
 *      env-string lengths -- which is the lesson.
 *
 * On the first run we observe argv[0] and pick a target a fixed BYTES_DELTA
 * (~128 bytes) below it, persist it in /challenge/.target via the inherited
 * FD, and tell the user. On subsequent runs we read the persisted target
 * and check. This keeps the required pad humanly typable instead of forcing
 * an arbitrary ~40000-byte shift to a hardcoded address.
 *
 * Why memfd-copy for the re-exec? Re-execing the SUID binary triggers
 * secureexec and clears ADDR_NO_RANDOMIZE. A memfd carries no SUID bit.
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
#define BYTES_DELTA 0x80     /* shift the target this many bytes below baseline */

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

static void inherit_target_fd(void) {
    int fd = open(TARGET_PATH, O_RDWR | O_CREAT, 0600);
    if (fd < 0) err(1, "open %s", TARGET_PATH);
    if (dup2(fd, TARGET_FD) < 0) err(1, "dup2 target");
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
    inherit_target_fd();

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

    unsigned long current = (unsigned long)argv[0];
    unsigned long target = read_persisted_target();
    if (target == 0) {
        target = current - BYTES_DELTA;
        write_persisted_target(target);
    }

    if (current != target) {
        long delta = (long)(current - target);
        fprintf(stderr,
                "argv[0] is at 0x%lx; I want it at 0x%lx.\n"
                "That's %ld bytes lower --- adjust your env padding.\n",
                current, target, delta);
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
