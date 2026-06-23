#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for callee-write. Loads the student's shared library and calls
 * solve(buf, len) where `buf` is the flag bytes and `len` is the flag
 * length. The flag arrives on stdin, not argv, so /proc/self/cmdline does
 * not expose it. The student's solve is expected to `write` the buffer to
 * stdout, so a correct solve makes the flag appear naturally on the
 * learner's terminal.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)
#define FLAG_CAPACITY 4096
#define DEBUG_FLAG "pwn.college{PLACEHOLDER}"

static char flagbuf[FLAG_CAPACITY];
static size_t flaglen;

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

static void use_debug_flag(void) {
    flaglen = sizeof(DEBUG_FLAG) - 1;
    memcpy(flagbuf, DEBUG_FLAG, flaglen);
    close(0);
    LOG("debugger detected; using placeholder flag bytes for this harness run.");
}

static void read_flag_from_stdin(void) {
    if (is_traced()) {
        use_debug_flag();
        return;
    }

    ssize_t n;
    while (flaglen < sizeof flagbuf && (n = read(0, flagbuf + flaglen, sizeof flagbuf - flaglen)) > 0) {
        flaglen += n;
    }
    if (n < 0) {
        err(2, "read flag");
    }
    if (flaglen == sizeof flagbuf) {
        errx(2, "flag buffer too small");
    }
    close(0);
}

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so   (the flag is read from stdin)\n", argv[0]);
        return 2;
    }

    read_flag_from_stdin();

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    void (*solve)(const char *, uint64_t) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("found solve at %p", (void *)solve);
    LOG("calling solve(<%zu-byte flag buffer>, %zu) --- your code should write those bytes to stdout:", flaglen, flaglen);

    solve(flagbuf, flaglen);

    LOG("solve() returned. (If your write was correct, the flag printed above.)");
    return 0;
}
