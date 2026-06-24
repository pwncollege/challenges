#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for stale-stack-data. The student's solve(read_flag) receives a
 * function pointer. read_flag copies the padded flag into its own stack frame
 * and returns, leaving stale bytes for solve to write out.
 */

#define FLAG_LEN 128
#define DEBUG_FLAG "pwn.college{PLACEHOLDER}"

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

char flag_buf[FLAG_LEN];
int read_flag_ran = 0;

extern long read_flag(void);

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

static int use_debug_flag(void) {
    if (!is_traced()) return 0;

    memset(flag_buf, 0, sizeof flag_buf);
    memcpy(flag_buf, DEBUG_FLAG, sizeof(DEBUG_FLAG) - 1);
    flag_buf[sizeof(DEBUG_FLAG) - 1] = '\n';
    close(0);
    LOG("debugger detected; using placeholder flag bytes for this harness run.");
    return 1;
}

static void read_exact_flag(void) {
    if (use_debug_flag()) {
        return;
    }

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

    LOG("reading a %d-byte padded flag buffer into the harness ...", FLAG_LEN);
    read_exact_flag();
    close(0);

    LOG("calling solve(read_flag) --- your code receives the read_flag function pointer in rdi");
    LOG("read_flag returns 0, but leaves a %d-byte stale flag buffer at [rsp-0x88] from solve's view", FLAG_LEN);
    LOG("call read_flag, then write those stale bytes to stdout:");

    solve(read_flag);

    if (!read_flag_ran) {
        LOG("your solve returned without calling read_flag");
        return 1;
    }

    LOG("solve() returned after calling read_flag.");
    return 0;
}
