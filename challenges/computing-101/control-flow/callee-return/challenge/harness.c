#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/*
 * Harness for callee-return. Loads the student's shared library, calls
 * solve(secret), and prints the flag if `solve` returns the secret back
 * unchanged. The secret is a random 64-bit value passed as argv[2] (so a
 * hardcoded `mov rax, N; ret` only "wins" with negligible probability),
 * and the flag is passed as argv[3].
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s lib.so secret flag\n", argv[0]);
        return 2;
    }

    uint64_t secret = strtoull(argv[2], NULL, 0);
    const char *flag = argv[3];

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    uint64_t (*solve)(uint64_t) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("found solve at %p", (void *)solve);
    LOG("calling solve(0x%lx) --- your code should return that value back unchanged in rax", secret);
    fflush(stderr);

    uint64_t got = solve(secret);

    LOG("solve() returned 0x%lx", got);
    if (got == secret) {
        LOG("match! return value == secret. here is the flag:");
        fflush(stderr);
        printf("%s\n", flag);
        return 0;
    }
    LOG("mismatch: you returned 0x%lx (%lu), but we sent in 0x%lx (%lu).",
        got, got, secret, secret);
    LOG("return the secret back, untouched!");
    return 1;
}
