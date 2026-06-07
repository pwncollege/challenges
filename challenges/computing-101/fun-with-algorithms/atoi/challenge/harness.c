#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

/*
 * Harness for the atoi levels. Loads the student's shared library and calls
 *   long atoi(const char *s)
 * on a number handed to us as text (argv[2]). atoi must return the parsed
 * integer in rax.
 *
 * We report that raw 64-bit return value to the checker over stdout (exactly 8
 * little-endian bytes) and let the checker --- a separate, privileged process
 * --- decide whether it is correct. Because the flag never enters this
 * (unprivileged) process, an atoi that tries to read or print the flag instead
 * of doing the conversion has nothing to steal.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

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
    LOG("resolving `atoi` symbol ...");
    long (*atoi_fn)(const char *) = (long (*)(const char *))dlsym(h, "atoi");
    if (!atoi_fn) {
        LOG("missing `atoi` symbol --- did you `.global atoi` in your assembly?");
        return 2;
    }

    LOG("calling atoi(\"%s\") --- your code returns the parsed integer in rax", numstr);
    long r = atoi_fn(numstr);
    LOG("atoi returned %ld", r);

    uint64_t v = (uint64_t)r;
    if (write(1, &v, sizeof v) != (ssize_t)sizeof v) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
