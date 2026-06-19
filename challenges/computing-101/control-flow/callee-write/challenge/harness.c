#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <stdint.h>
#include <stdio.h>
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

static char flagbuf[FLAG_CAPACITY];
static size_t flaglen;

static void read_flag_from_stdin(void) {
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
