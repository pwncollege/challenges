#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

/*
 * Harness for the argv-array levels. Loads the student's shared library and
 * calls
 *   long solve(char **nums, long count)
 * where `nums` is an array of `count` number strings (handed to us as our own
 * argv[2..]). solve must return its integer result in rax.
 *
 * As with the earlier levels, we report that raw 64-bit return value to the
 * checker over stdout (exactly 8 little-endian bytes) and let the checker --- a
 * separate, privileged process --- decide whether it is correct. The flag
 * never enters this (unprivileged) process.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc < 3) {
        fprintf(stderr, "usage: %s lib.so number [number ...]\n", argv[0]);
        return 2;
    }
    char **nums = &argv[2];
    long count = argc - 2;

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    long (*solve)(char **, long) = (long (*)(char **, long))dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }

    fprintf(stderr, "[harness] calling solve(nums, %ld) with nums =", count);
    for (long i = 0; i < count; i++)
        fprintf(stderr, " \"%s\"", nums[i]);
    fputc('\n', stderr);

    long r = solve(nums, count);
    LOG("solve returned %ld", r);

    uint64_t v = (uint64_t)r;
    if (write(1, &v, sizeof v) != (ssize_t)sizeof v) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
