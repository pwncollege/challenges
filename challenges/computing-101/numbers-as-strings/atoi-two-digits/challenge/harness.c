#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/random.h>
#include <unistd.h>

/*
 * Harness for atoi-two-digits. The student's library exports two functions, and
 * we test each one separately:
 *   long atoi_digit(const char *s)   -- value of one digit (as in the last level)
 *   long atoi(const char *s)         -- value of a two-character number
 *
 * Invoked as:  harness <lib.so> <funcname> <input>
 * It resolves <funcname>, calls it on <input> through call_fn (shim.S), checks
 * that the call preserved the callee-saved registers and rsp (both functions
 * must honor the calling convention), and reports the raw 64-bit return value to the
 * checker over stdout (exactly 8 little-endian bytes). The flag never enters
 * this (unprivileged) process.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

/* Provided by shim.S: seeds the register state, calls fn(s), then records it. */
extern long call_fn(long (*fn)(const char *), const char *s);
extern uint64_t cc_seen[6];
extern uint64_t cc_incoming[8];
extern uint64_t cc_expected_rsp;
extern uint64_t cc_seen_rsp;

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

static int check_call_state(const char *fname) {
    static const uint64_t cc_expected[6] = {
        0x1111111111111111ULL, 0xb0b0b0b0b0b0b0b0ULL, 0x1212121212121212ULL,
        0x1313131313131313ULL, 0x1414141414141414ULL, 0x1515151515151515ULL,
    };
    static const char *ccname[6] = {"rbx", "rbp", "r12", "r13", "r14", "r15"};

    for (size_t i = 0; i < sizeof cc_seen / sizeof cc_seen[0]; i++) {
        if (cc_seen[i] != cc_expected[i]) {
            LOG("your %s clobbered %s without restoring it.", fname, ccname[i]);
            LOG("a function must preserve the callee-saved registers (rbx, rbp, r12-r15) for its caller ---");
            LOG("push them on entry and pop them before you ret, or just don't use them.");
            return -1;
        }
    }
    if (cc_seen_rsp != cc_expected_rsp) {
        LOG("your %s returned with rsp = 0x%lx, but its caller expected 0x%lx.",
            fname, cc_seen_rsp, cc_expected_rsp);
        LOG("balance every stack allocation and push before you ret.");
        return -1;
    }
    return 0;
}

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 4) {
        fprintf(stderr, "usage: %s lib.so funcname input\n", argv[0]);
        return 2;
    }
    const char *fname = argv[2];
    const char *input = argv[3];

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `%s` symbol ...", fname);
    long (*fn)(const char *) = (long (*)(const char *))dlsym(h, fname);
    if (!fn) {
        LOG("missing `%s` symbol --- did you `.global %s` in your assembly?", fname, fname);
        return 2;
    }

    LOG("calling %s(\"%s\") --- your code returns the value in rax", fname, input);
    if (prepare_call() != 0) {
        return 2;
    }
    long r = call_fn(fn, input);
    LOG("%s returned %ld", fname, r);

    if (check_call_state(fname) != 0) {
        return 1;
    }

    uint64_t v = (uint64_t)r;
    if (write(1, &v, sizeof v) != (ssize_t)sizeof v) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
