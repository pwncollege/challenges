#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * Harness for itoa-digit. Loads the student's shared library and calls
 *   long itoa_digit(long value)
 * on a single-digit value (0-9, handed to us as text). itoa_digit must return
 * that digit's ASCII character in rax.
 *
 * The call goes through call_fn (shim.S), which seeds the callee-saved registers
 * (rbx, r12-r15) and checks they survive --- itoa_digit is a function later
 * levels reuse, so it must honor the calling convention. We report the raw
 * 64-bit return value to the checker over stdout (exactly 8 little-endian bytes).
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

extern long call_fn(long (*fn)(long), long arg);  /* seeds rbx,r12-r15; calls fn(arg) */
extern uint64_t cc_seen[5];

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so value\n", argv[0]);
        return 2;
    }
    long value = strtol(argv[2], NULL, 10);

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `itoa_digit` symbol ...");
    long (*itoa_digit)(long) = (long (*)(long))dlsym(h, "itoa_digit");
    if (!itoa_digit) {
        LOG("missing `itoa_digit` symbol --- did you `.global itoa_digit` in your assembly?");
        return 2;
    }

    LOG("calling itoa_digit(%ld) --- your code returns the digit's ASCII character in rax", value);
    long r = call_fn(itoa_digit, value);
    LOG("itoa_digit returned %ld ('%c')", r, (r >= 0x20 && r < 0x7f) ? (char)r : '?');

    static const uint64_t cc_expected[5] = {
        0x1111111111111111ULL, 0x1212121212121212ULL, 0x1313131313131313ULL,
        0x1414141414141414ULL, 0x1515151515151515ULL,
    };
    static const char *ccname[5] = {"rbx", "r12", "r13", "r14", "r15"};
    for (int i = 0; i < 5; i++) {
        if (cc_seen[i] != cc_expected[i]) {
            LOG("your itoa_digit clobbered %s without restoring it.", ccname[i]);
            LOG("a function must preserve the callee-saved registers (rbx, r12-r15) for its caller ---");
            LOG("push them on entry and pop them before you ret, or just don't use them.");
            return 1;
        }
    }

    uint64_t v = (uint64_t)r;
    if (write(1, &v, sizeof v) != (ssize_t)sizeof v) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
