#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for callee-return. Loads the student's shared library, calls
 * solve(secret), and prints the flag if `solve` returns the secret back
 * unchanged. The secret is a random 64-bit value passed as argv[2] (so a
 * hardcoded `mov rax, N; ret` only "wins" with negligible probability),
 * and the flag is read from stdin so it never appears in argv (and
 * therefore never in bash's "Segmentation fault" message on a broken
 * solve).
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so secret   (flag is read from stdin)\n", argv[0]);
        return 2;
    }

    uint64_t secret = strtoull(argv[2], NULL, 0);

    char flag[256];
    ssize_t total = 0;
    ssize_t n;
    while ((n = read(0, flag + total, sizeof(flag) - 1 - total)) > 0) {
        total += n;
        if (total >= (ssize_t)sizeof(flag) - 1) break;
    }
    if (total <= 0) {
        fprintf(stderr, "expected the flag on stdin, but got nothing\n");
        return 2;
    }
    flag[total] = 0;
    while (total > 0 && (flag[total - 1] == '\n' || flag[total - 1] == '\r')) flag[--total] = 0;

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

    uint64_t got = solve(secret);

    LOG("solve() returned 0x%lx", got);
    if (got == secret) {
        LOG("match! return value == secret. here is the flag:");
        printf("%s\n", flag);
        return 0;
    }
    LOG("mismatch: you returned 0x%lx (%lu), but we sent in 0x%lx (%lu).",
        got, got, secret, secret);
    LOG("return the secret back, untouched!");
    return 1;
}
