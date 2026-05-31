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

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s lib.so secret flag\n", argv[0]);
        return 2;
    }

    uint64_t secret = strtoull(argv[2], NULL, 0);
    const char *flag = argv[3];

    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 2;
    }
    uint64_t (*solve)(uint64_t) = dlsym(h, "solve");
    if (!solve) {
        fprintf(stderr, "missing `solve` symbol\n");
        return 2;
    }

    uint64_t got = solve(secret);
    if (got == secret) {
        printf("%s\n", flag);
        return 0;
    }
    printf("You returned 0x%lx (%lu), but we sent in 0x%lx (%lu) --- "
           "return the secret back, untouched!\n",
           got, got, secret, secret);
    return 1;
}
