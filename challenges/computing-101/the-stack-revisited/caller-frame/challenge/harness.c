#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

extern uint64_t caller(uint64_t (*solve)(void), uint64_t secret);

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so\n", argv[0]);
        return 2;
    }

    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 2;
    }
    uint64_t (*solve)(void) = (uint64_t (*)(void))dlsym(h, "solve");
    if (!solve) {
        fprintf(stderr, "missing `solve` symbol\n");
        return 2;
    }

    uint64_t secret;
    int rf = open("/dev/urandom", O_RDONLY);
    if (rf < 0 || read(rf, &secret, sizeof secret) != (ssize_t)sizeof secret) {
        fprintf(stderr, "could not read /dev/urandom\n");
        return 2;
    }
    close(rf);

    uint64_t got = caller(solve, secret);
    if (got == secret) {
        printf("OK secret=0x%lx\n", secret);
        return 0;
    } else {
        printf("WRONG expected=0x%lx got=0x%lx\n", secret, got);
        return 1;
    }
}
