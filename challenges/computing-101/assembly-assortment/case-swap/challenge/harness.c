#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Harness for the case-change levels. Decodes the hex byte-string in argv[2]
 * into a NUL-terminated buffer and calls
 *   void str_swapcase(char *s)
 * which must walk the string until the NUL byte, transforming each character
 * in place (and returns nothing meaningful).
 *
 * The case transforms preserve length, so the modified n bytes are written
 * back to the checker on stdout; the checker independently computes the right
 * answer and decides. The flag never enters this unprivileged process.
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
    char *buf = malloc(n + 1);
    if (!buf) return 2;
    for (size_t i = 0; i < n; i++) {
        int hi = hexval((unsigned char)argv[2][2 * i]);
        int lo = hexval((unsigned char)argv[2][2 * i + 1]);
        if (hi < 0 || lo < 0) {
            LOG("bad hex digit in input");
            return 2;
        }
        buf[i] = (char)(hi << 4 | lo);
    }
    buf[n] = 0;

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `str_swapcase` symbol ...");
    void (*str_swapcase)(char *) = (void (*)(char *))dlsym(h, "str_swapcase");
    if (!str_swapcase) {
        LOG("missing `str_swapcase` symbol --- did you `.global str_swapcase` in your assembly?");
        return 2;
    }
    LOG("calling str_swapcase(s) --- your code transforms the %zu-byte string in place", n);
    str_swapcase(buf);
    LOG("str_swapcase returned; reporting the modified bytes to the checker");

    if (n && write(1, buf, n) != (ssize_t)n) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
