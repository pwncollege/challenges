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

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so flag\n", argv[0]);
        return 2;
    }
    const char *flag = argv[2];
    size_t len = strlen(flag);

    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 2;
    }
    void (*solve)(const char *, uint64_t) = dlsym(h, "solve");
    if (!solve) {
        fprintf(stderr, "missing `solve` symbol\n");
        return 2;
    }

    solve(flag, len);
    return 0;
}
