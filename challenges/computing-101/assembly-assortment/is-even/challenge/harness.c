#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * Harness for the assembly-assortment bitwise levels (and/or/shl/shr). Loads the student's shared
 * library and calls
 *   long solve(long x)
 * on a single 64-bit value handed to us as text (argv[2], decimal or 0x-hex).
 * solve must return its result in rax.
 *
 * We report the raw 64-bit return value to the checker over stdout (exactly 8
 * little-endian bytes) and let the checker --- a separate, privileged process
 * --- decide whether it is correct. Because the flag never enters this
 * (unprivileged) process, a solve that tries to read or print the flag instead
 * of doing the computation has nothing to steal.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so value\n", argv[0]);
        return 2;
    }
    uint64_t x = strtoull(argv[2], NULL, 0);

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    uint64_t (*solve)(uint64_t) = (uint64_t (*)(uint64_t))dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("calling solve(0x%lx) --- your code returns its result in rax", x);
    uint64_t r = solve(x);
    LOG("solve returned 0x%lx", r);

    if (write(1, &r, sizeof r) != (ssize_t)sizeof r) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
