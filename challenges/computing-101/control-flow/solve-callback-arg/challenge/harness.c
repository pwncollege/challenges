#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>

/*
 * Harness for solve-callback-arg. The student's `solve(callback)` must invoke
 * the function pointer it receives in rdi, passing 1337 as the callback's
 * first argument (also in rdi).
 *
 * `force_align_arg_pointer` makes gcc emit a prologue that realigns rsp to
 * 16 bytes, so the callback can safely call printf even when the student's
 * `call <reg>` lands here with an 8-byte-misaligned rsp.
 */

#define EXPECTED 1337

static const char *flag;
static int called = 0;

static void __attribute__((force_align_arg_pointer)) cb(uint64_t arg) {
    called = 1;
    if (arg == EXPECTED) {
        printf("%s\n", flag);
    } else {
        printf("You passed %lu (0x%lx) to the callback, but it needs to be %d (0x%x)!\n",
               arg, arg, EXPECTED, EXPECTED);
    }
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so flag\n", argv[0]);
        return 2;
    }
    flag = argv[2];

    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 2;
    }
    void (*solve)(void (*)(uint64_t)) = dlsym(h, "solve");
    if (!solve) {
        fprintf(stderr, "missing `solve` symbol\n");
        return 2;
    }

    solve(cb);
    if (!called) {
        printf("Your `solve` returned without calling the callback in rdi.\n");
    }
    return 0;
}
