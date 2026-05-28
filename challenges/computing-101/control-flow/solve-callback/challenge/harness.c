#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

/*
 * Harness for solve-callback. The student's `solve(callback)` must invoke the
 * function pointer it receives in rdi. The callback below just stashes a token
 * (passed in argv[2]) into a static buffer; we print it from main() after the
 * call returns. Doing the printing in main() avoids triggering aligned-SSE
 * code paths inside the callback, which the student's `call rdi` would crash
 * on if they don't align rsp -- a wrinkle that isn't the lesson here.
 */

static char captured[256];
static int captured_len = 0;
static const char *token;
static int token_len;

static void cb(void) {
    if (captured_len + token_len <= (int)sizeof(captured)) {
        memcpy(captured + captured_len, token, token_len);
        captured_len += token_len;
    }
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so token\n", argv[0]);
        return 2;
    }
    token = argv[2];
    token_len = strlen(token);

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

    if (captured_len > 0) {
        fwrite(captured, 1, captured_len, stdout);
    }
    return 0;
}
