#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for callee-callback. The student's `solve(callback)` must invoke the
 * function pointer it receives in rdi. The callback below prints the flag,
 * which arrives on stdin instead of argv so /proc/self/cmdline does not expose
 * it. A successful solve makes the flag appear naturally.
 *
 * `force_align_arg_pointer` makes gcc emit a prologue that realigns rsp to
 * 16 bytes, so the callback can safely do anything (SSE, printf, etc.) even
 * when the student's `call rdi` lands here with an 8-byte-misaligned rsp.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)
#define FLAG_CAPACITY 4096
#define DEBUG_FLAG "pwn.college{PLACEHOLDER}"

static char flagbuf[FLAG_CAPACITY];
static size_t flaglen;
static int callback_ran = 0;

static int is_traced(void) {
    int fd = open("/proc/self/status", O_RDONLY);
    if (fd < 0) return 0;
    char buf[4096];
    ssize_t n = read(fd, buf, sizeof buf - 1);
    close(fd);
    if (n <= 0) return 0;
    buf[n] = 0;
    char *p = strstr(buf, "TracerPid:");
    return p && atoi(p + sizeof("TracerPid:") - 1) != 0;
}

static void use_debug_flag(void) {
    flaglen = sizeof(DEBUG_FLAG) - 1;
    memcpy(flagbuf, DEBUG_FLAG, flaglen);
    close(0);
    LOG("debugger detected; using placeholder flag bytes for this harness run.");
}

static void read_flag_from_stdin(void) {
    if (is_traced()) {
        use_debug_flag();
        return;
    }

    ssize_t n;
    while (flaglen < sizeof flagbuf && (n = read(0, flagbuf + flaglen, sizeof flagbuf - flaglen)) > 0) {
        flaglen += n;
    }
    if (n < 0) {
        err(2, "read flag");
    }
    if (flaglen == sizeof flagbuf) {
        errx(2, "flag buffer too small");
    }
    close(0);
}

static void __attribute__((force_align_arg_pointer)) cb(void) {
    callback_ran = 1;
    fwrite(flagbuf, 1, flaglen, stdout);
    fputc('\n', stdout);
}

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so   (the flag is read from stdin)\n", argv[0]);
        return 2;
    }

    read_flag_from_stdin();

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
