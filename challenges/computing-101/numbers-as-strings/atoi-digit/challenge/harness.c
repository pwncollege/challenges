#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

/*
 * Harness for atoi-digit. Loads the student's shared library and calls
 *   long atoi_digit(const char *s)
 * on a single digit handed to us as text (argv[2]). atoi_digit must return the
 * digit's value in rax.
 *
 * The call goes through call_atoi_digit (shim.S), which first seeds the
 * callee-saved registers (rbx, r12-r15) with sentinels and then checks they
 * survive the call --- atoi_digit is a function later levels will reuse, so it
 * must honor the calling convention.
 *
 * We report the raw 64-bit return value to the checker over stdout (exactly 8
 * little-endian bytes) and let the checker --- a separate, privileged process
 * --- decide whether it is correct. Because the flag never enters this
 * (unprivileged) process, an atoi_digit that tries to read or print the flag
 * instead of doing the conversion has nothing to steal.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

/* Provided by shim.S: seeds rbx,r12-r15, calls fn(s), records them in cc_seen. */
extern long call_atoi_digit(long (*fn)(const char *), const char *s);
extern uint64_t cc_seen[5];

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so number\n", argv[0]);
        return 2;
    }
    const char *numstr = argv[2];

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `atoi_digit` symbol ...");
    long (*atoi_digit)(const char *) = (long (*)(const char *))dlsym(h, "atoi_digit");
    if (!atoi_digit) {
        LOG("missing `atoi_digit` symbol --- did you `.global atoi_digit` in your assembly?");
        return 2;
    }

    LOG("calling atoi_digit(\"%s\") --- your code returns the digit's value in rax", numstr);
    long r = call_atoi_digit(atoi_digit, numstr);
    LOG("atoi_digit returned %ld", r);

    // atoi_digit must preserve the callee-saved registers for its caller.
    static const uint64_t cc_expected[5] = {
        0x1111111111111111ULL, 0x1212121212121212ULL, 0x1313131313131313ULL,
        0x1414141414141414ULL, 0x1515151515151515ULL,
    };
    static const char *ccname[5] = {"rbx", "r12", "r13", "r14", "r15"};
    for (int i = 0; i < 5; i++) {
        if (cc_seen[i] != cc_expected[i]) {
            LOG("your atoi_digit clobbered %s without restoring it.", ccname[i]);
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
