#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for build-frame. Decodes the hex byte-string in argv[2] into a
 * buffer and calls
 *   long solve(unsigned char *data, long n)
 * which must return, in rax, the number of distinct byte values in data[0..n).
 *
 * The 64-bit return value is reported to the checker as 8 little-endian bytes
 * on stdout; the checker independently computes the right answer and decides.
 * The flag never enters this unprivileged process.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

static int hexval(int c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so hexbytes\n", argv[0]);
        return 2;
    }

    size_t hexlen = strlen(argv[2]);
    if (hexlen % 2 != 0) {
        LOG("hex input has an odd number of digits");
        return 2;
    }
    size_t n = hexlen / 2;
    unsigned char *data = malloc(n ? n : 1);
    if (!data) return 2;
    for (size_t i = 0; i < n; i++) {
        int hi = hexval((unsigned char)argv[2][2 * i]);
        int lo = hexval((unsigned char)argv[2][2 * i + 1]);
        if (hi < 0 || lo < 0) {
            LOG("bad hex digit in input");
            return 2;
        }
        data[i] = (unsigned char)(hi << 4 | lo);
    }

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    long (*solve)(unsigned char *, long) = (long (*)(unsigned char *, long))dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("calling solve(data, %zu) --- your code returns the count of distinct byte values in rax", n);
    long r = solve(data, (long)n);
    LOG("solve returned %ld", r);

    uint64_t v = (uint64_t)r;
    if (write(1, &v, sizeof v) != (ssize_t)sizeof v) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
