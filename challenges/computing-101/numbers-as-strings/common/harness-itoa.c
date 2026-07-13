#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <unistd.h>

/*
 * Harness for the string-producing itoa levels (itoa-two-digits, itoa, and
 * itoa-negative all share it). Loads the student's library and calls
 *   long itoa(long value, char *buf)
 * which writes the decimal text of `value` into `buf` and returns the number of
 * characters written. We report those exact bytes to the checker over stdout.
 *
 * The call goes through call_fn2 (shim.S), which seeds the incoming register
 * state and checks that the callee-saved registers and rsp survive.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)
#define BUFCAP 64

extern long call_fn2(void *fn, long value, void *buf);
extern uint64_t cc_seen[6];
extern uint64_t cc_incoming[8];
extern uint64_t cc_expected_rsp;
extern uint64_t cc_seen_rsp;

static char outbuf[BUFCAP];

static int prepare_call(void) {
    if (getrandom(cc_incoming, sizeof cc_incoming, 0) != (ssize_t)sizeof cc_incoming) {
        LOG("getrandom failed");
        return -1;
    }

    /* Keep accidental pointer use deterministic: these values vary, but none
     * is a canonical 64-bit x86 address. */
    for (size_t i = 0; i < sizeof cc_incoming / sizeof cc_incoming[0]; i++)
        cc_incoming[i] = (cc_incoming[i] & 0x0000ffffffffffffULL) | 0x5a5a000000000000ULL;
    return 0;
}

static int check_call_state(void) {
    static const uint64_t cc_expected[6] = {
        0x1111111111111111ULL, 0xb0b0b0b0b0b0b0b0ULL, 0x1212121212121212ULL,
        0x1313131313131313ULL, 0x1414141414141414ULL, 0x1515151515151515ULL,
    };
    static const char *ccname[6] = {"rbx", "rbp", "r12", "r13", "r14", "r15"};

    for (size_t i = 0; i < sizeof cc_seen / sizeof cc_seen[0]; i++) {
        if (cc_seen[i] != cc_expected[i]) {
            LOG("your itoa clobbered %s without restoring it.", ccname[i]);
            LOG("a function must preserve the callee-saved registers (rbx, rbp, r12-r15) for its caller ---");
            LOG("push them on entry and pop them before you ret, or just don't use them.");
            return -1;
        }
    }
    if (cc_seen_rsp != cc_expected_rsp) {
        LOG("your itoa returned with rsp = 0x%lx, but its caller expected 0x%lx.",
            cc_seen_rsp, cc_expected_rsp);
        LOG("balance every stack allocation and push before you ret.");
        return -1;
    }
    return 0;
}

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
    LOG("resolving `itoa` symbol ...");
    void *itoa = dlsym(h, "itoa");
    if (!itoa) {
        LOG("missing `itoa` symbol --- did you `.global itoa` in your assembly?");
        return 2;
    }

    memset(outbuf, 0, sizeof outbuf);
    LOG("calling itoa(%ld, buf) --- your code writes the digits to buf and returns the count", value);
    if (prepare_call() != 0) {
        return 2;
    }
    long len = call_fn2(itoa, value, outbuf);
    LOG("itoa returned %ld; buf = \"%.*s\"", len, (len > 0 && len <= BUFCAP) ? (int)len : 0, outbuf);

    if (len < 0 || len > BUFCAP) {
        LOG("invalid return count: itoa returned %ld, but it must return between 0 and %d.", len, BUFCAP);
        LOG("return the number of characters written in rax.");
        return 1;
    }

    if (check_call_state() != 0) {
        return 1;
    }

    if (write(1, outbuf, (size_t)len) != (ssize_t)len) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
