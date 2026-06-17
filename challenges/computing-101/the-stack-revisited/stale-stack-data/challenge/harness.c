#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

/*
 * Harness for stale-stack-data. The student's solve(read_flag) receives a
 * function pointer. read_flag copies the padded flag into its own stack frame
 * and returns, leaving stale bytes for solve to write out.
 */

#define FLAG_LEN 128

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

char flag_buf[FLAG_LEN];
int read_flag_ran = 0;

extern long read_flag(void);

static void read_exact_flag(void) {
    ssize_t got = 0;
    while (got < FLAG_LEN) {
        ssize_t n = read(0, flag_buf + got, FLAG_LEN - got);
        if (n < 0) {
            err(2, "read flag");
        }
        if (n == 0) {
            errx(2, "short flag read (%zd of %d bytes)", got, FLAG_LEN);
        }
        got += n;
    }
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        errx(2, "usage: %s lib.so", argv[0]);
    }

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        errx(2, "dlopen failed: %s", dlerror());
    }
    LOG("resolving `solve` symbol ...");
    void (*solve)(long (*)(void)) = (void (*)(long (*)(void)))dlsym(h, "solve");
    if (!solve) {
        errx(2, "missing `solve` symbol --- did you `.global solve` in your assembly?");
    }

    LOG("reading %d bytes of flag into the harness ...", FLAG_LEN);
    read_exact_flag();
    close(0);

    LOG("calling solve(read_flag) --- your code receives the read_flag function pointer in rdi");
    LOG("read_flag returns 0, but leaves %d stale flag bytes at [rsp-0x88] from solve's view", FLAG_LEN);
    LOG("call read_flag, then write those stale bytes to stdout:");

    solve(read_flag);

    if (!read_flag_ran) {
        LOG("your solve returned without calling read_flag");
        return 1;
    }

    LOG("solve() returned after calling read_flag.");
    return 0;
}
