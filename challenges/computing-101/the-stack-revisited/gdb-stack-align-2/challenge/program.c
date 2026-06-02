/* Sequel to ../gdb-stack-align. Same SUID + memfd re-exec machinery (see that
 * program.c for the rationale); the lesson is generalized.
 *
 * In gdb-stack-align the gdb wrapper preserved your shell's environment
 * (exec-suid --environ all), so gdb's argv[0] differed from your shell's by
 * only the handful of variables gdb adds --- a small shift you closed by
 * *padding* your existing shell environment.
 *
 * Here the wrapper does NOT preserve your environment: gdb runs with its own
 * scrubbed environment, which looks nothing like your shell's (different
 * HOME/USER/PATH, none of your shell's vars, plus gdb's own). You cannot pad
 * your shell to match that --- the variables themselves differ. The general
 * technique is to throw your environment away and rebuild it deterministically:
 *
 *   1. Run /challenge/program under gdb --- it captures its argv[0] as the
 *      target.
 *   2. Quit gdb. Outside gdb we REQUIRE exactly one environment variable, which
 *      forces `env -i` (wipe the environment, start from nothing) plus one
 *      padded variable. Grow that variable until argv[0] lands on the target.
 *
 * Only env *string* bytes move argv[0], so a single padded variable can match
 * gdb's many-variable environment exactly --- the variable count is irrelevant.
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

static int env_count(void) {
    int n = 0;
    for (char **e = environ; *e; e++) n++;
    return n;
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
                "Quit gdb. My environment in here is nothing like your shell's, so you\n"
                "can't pad your shell to match it. Outside gdb I require exactly ONE\n"
                "environment variable: wipe your environment and rebuild it with one\n"
                "padded variable ---\n"
                "    env -i FOO=xxxxxxxx /challenge/program\n"
                "--- then grow the x's until argv[0] lands here.\n",
                current);
        return 1;
    }

    int n = env_count();
    if (n != 1) {
        fprintf(stderr,
                "You're running me with %d environment variables, but I need exactly 1! "
                "Clear the environment and set one variable, then rerun me!\n",
                n);
        return 1;
    }

    unsigned long target = read_persisted_target();
    if (target == 0) {
        fprintf(stderr,
                "argv[0] is at 0x%lx (one env var), but I don't have a target yet.\n"
                "Run me under gdb first (`gdb /challenge/program`, then `run`) so I can\n"
                "capture the gdb-context argv[0].\n",
                current);
        return 1;
    }

    if (current != target) {
        long delta = (long)(current - target);
        if (delta > 0) {
            fprintf(stderr,
                    "argv[0] is at 0x%lx (one env var); I want it at 0x%lx (where gdb "
                    "put it).\nThat's %ld bytes lower --- add %ld more characters to "
                    "your one variable.\n",
                    current, target, delta, delta);
        } else {
            fprintf(stderr,
                    "argv[0] is at 0x%lx (one env var); I want it at 0x%lx (where gdb "
                    "put it).\nThat's %ld bytes higher --- you've overshot; shorten "
                    "your variable.\n",
                    current, target, -delta);
        }
        return 1;
    }

    char buf[256];
    ssize_t n2 = read(FLAG_FD, buf, sizeof buf);
    if (n2 > 0) write(1, buf, n2);
    return 0;
}

int main(int argc, char **argv) {
    if (re_exec_phase()) return challenge_phase(argc, argv);
    setup_phase(argv);
    return 1; /* unreachable */
}
