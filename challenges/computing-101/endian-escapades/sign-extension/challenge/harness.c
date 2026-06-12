#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3) {
        fprintf(stderr, "usage: %s lib.so byte\n", argv[0]);
        return 2;
    }

    uint8_t value = strtoull(argv[2], NULL, 0) & 0xff;

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }

    LOG("resolving `solve` symbol ...");
    int64_t (*solve)(uint8_t *) = (int64_t (*)(uint8_t *))dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }

    LOG("calling solve(&value), where value is 0x%02x", value);
    uint64_t result = (uint64_t)solve(&value);
    LOG("solve returned 0x%lx", result);

    if (write(1, &result, sizeof result) != (ssize_t)sizeof result) {
        LOG("failed to report result to checker");
        return 2;
    }
    return 0;
}
