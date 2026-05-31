#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

#define FLAG_LEN 64

extern void caller(void (*solve)(void), const char *flag_buf);

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
    void (*solve)(void) = (void (*)(void))dlsym(h, "solve");
    if (!solve) {
        fprintf(stderr, "missing `solve` symbol\n");
        return 2;
    }

    char flag_buf[FLAG_LEN];
    ssize_t got = 0;
    while (got < FLAG_LEN) {
        ssize_t n = read(0, flag_buf + got, FLAG_LEN - got);
        if (n <= 0) {
            fprintf(stderr, "harness: short flag read (%zd of %d bytes)\n", got, FLAG_LEN);
            return 2;
        }
        got += n;
    }

    caller(solve, flag_buf);
    return 0;
}
