#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>

/*
 * Harness for callee-callback. The student's `solve(callback)` must invoke
 * the function pointer it receives in rdi. The callback below just prints
 * the flag (read from stdin) to stdout, so a successful solve makes the flag
 * appear naturally. We read the flag from stdin --- not argv --- so bash's
 * "Segmentation fault" message on a broken solve never exposes the flag.
 *
 * `force_align_arg_pointer` makes gcc emit a prologue that realigns rsp to
 * 16 bytes, so the callback can safely do anything (SSE, printf, etc.) even
 * when the student's `call rdi` lands here with an 8-byte-misaligned rsp.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

static char flag[256];
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

    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so   (flag is read from stdin)\n", argv[0]);
        return 2;
    }

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
