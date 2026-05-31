#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>

/*
 * Harness for solve-callback. The student's `solve(callback)` must invoke the
 * function pointer it receives in rdi. The callback below just prints the
 * token (passed in argv[2]) to stdout.
 *
 * `force_align_arg_pointer` makes gcc emit a prologue that realigns rsp to
 * 16 bytes, so the callback can safely do anything (SSE, printf, etc.) even
 * when the student's `call rdi` lands here with an 8-byte-misaligned rsp.
 */

static const char *token;

static void __attribute__((force_align_arg_pointer)) cb(void) {
    printf("%s", token);
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so token\n", argv[0]);
        return 2;
    }
    token = argv[2];

    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 2;
    }
    void (*solve)(void (*)(void)) = dlsym(h, "solve");
    if (!solve) {
        fprintf(stderr, "missing `solve` symbol\n");
        return 2;
    }

    solve(cb);
    return 0;
}
