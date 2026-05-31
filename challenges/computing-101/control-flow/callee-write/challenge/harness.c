#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/*
 * Harness for callee-write. Loads the student's shared library and calls
 * solve(buf, len) where `buf` is the flag bytes and `len` is the flag
 * length, both passed via argv. The student's solve is expected to
 * `write` the buffer to stdout, so a correct solve makes the flag
 * appear naturally on the learner's terminal.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so flag\n", argv[0]);
        return 2;
    }
    const char *flag = argv[2];
    size_t len = strlen(flag);

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
    LOG("calling solve(<%zu-byte flag buffer>, %zu) --- your code should write those bytes to stdout:", len, len);

    solve(flag, len);

    LOG("solve() returned. (If your write was correct, the flag printed above.)");
    return 0;
}
