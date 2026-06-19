#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

/*
 * Harness for callee-callback-arg. The student's `solve(callback)` must invoke
 * the function pointer it receives in rdi, passing 1337 as the callback's
 * first argument (also in rdi). The flag arrives on stdin, not argv, so
 * /proc/self/cmdline does not expose it.
 *
 * `force_align_arg_pointer` makes gcc emit a prologue that realigns rsp to
 * 16 bytes, so the callback can safely call printf even when the student's
 * `call <reg>` lands here with an 8-byte-misaligned rsp.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

#define EXPECTED 1337
#define FLAG_CAPACITY 4096

static char flagbuf[FLAG_CAPACITY];
static size_t flaglen;
static int called = 0;

static void read_flag_from_stdin(void) {
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

static void __attribute__((force_align_arg_pointer)) cb(uint64_t arg) {
    called = 1;
    if (arg == EXPECTED) {
        fwrite(flagbuf, 1, flaglen, stdout);
        fputc('\n', stdout);
    } else {
        printf("You passed %lu (0x%lx) to the callback, but it needs to be %d (0x%x)!\n",
               arg, arg, EXPECTED, EXPECTED);
    }
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
    void (*solve)(void (*)(uint64_t)) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("found solve at %p", (void *)solve);
    LOG("calling solve(callback) --- your code receives the callback in rdi");
    LOG("the callback prints the flag if you call it with rdi == %d, or a hint otherwise:", EXPECTED);

    solve(cb);

    if (called) {
        LOG("the callback ran. solve() returned cleanly.");
        return 0;
    }
    LOG("your `solve` returned without calling the callback in rdi.");
    LOG("save the function pointer somewhere safe (e.g. `mov rax, rdi`), set rdi = %d, then call.", EXPECTED);
    return 1;
}
