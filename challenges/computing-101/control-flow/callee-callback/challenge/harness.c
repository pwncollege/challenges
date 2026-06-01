#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>

/*
 * Harness for callee-callback. The student's `solve(callback)` must invoke the
 * function pointer it receives in rdi. The callback below just prints the
 * flag (passed in argv[2]) to stdout, so a successful solve makes the flag
 * appear naturally.
 *
 * `force_align_arg_pointer` makes gcc emit a prologue that realigns rsp to
 * 16 bytes, so the callback can safely do anything (SSE, printf, etc.) even
 * when the student's `call rdi` lands here with an 8-byte-misaligned rsp.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

static const char *flag;
static int callback_ran = 0;

static void __attribute__((force_align_arg_pointer)) cb(void) {
    callback_ran = 1;
    printf("%s\n", flag);
}

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
    flag = argv[2];

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    void (*solve)(void (*)(void)) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("found solve at %p", (void *)solve);
    LOG("calling solve(callback) --- your code receives the callback in rdi and should call it");
    LOG("if the callback runs, it prints the flag for you:");

    solve(cb);

    if (callback_ran) {
        LOG("the callback ran. solve() returned cleanly.");
        return 0;
    }
    LOG("your `solve` returned without calling the callback in rdi.");
    LOG("make sure your assembly does `call rdi` (or moves rdi elsewhere and calls from there).");
    return 1;
}
