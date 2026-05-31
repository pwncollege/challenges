#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for callee-write. Loads the student's shared library and calls
 * solve(buf, len) where `buf` is the flag bytes (read from stdin) and `len`
 * is its length. The student's solve is expected to `write` the buffer to
 * stdout, so a correct solve makes the flag appear naturally on the
 * learner's terminal.
 *
 * Why stdin and not argv? If the flag were in argv, bash's "Segmentation
 * fault" message on a deliberately-broken solve would expose the flag in
 * the displayed command-line. Reading from stdin keeps it out of argv.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so   (flag is read from stdin)\n", argv[0]);
        return 2;
    }

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

    char flag[256];
    ssize_t total = 0;
    ssize_t n;
    while ((n = read(0, flag + total, sizeof(flag) - total)) > 0) {
        total += n;
        if (total >= (ssize_t)sizeof(flag)) break;
    }
    if (total <= 0) {
        LOG("expected the flag on stdin, but got nothing.");
        return 2;
    }
    while (total > 0 && (flag[total - 1] == '\n' || flag[total - 1] == '\r')) total--;
    size_t len = (size_t)total;

    LOG("calling solve(<%zu-byte flag buffer>, %zu) --- your code should write those bytes to stdout:", len, len);

    solve(flag, len);

    LOG("solve() returned. (If your write was correct, the flag printed above.)");
    return 0;
}
