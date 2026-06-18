#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * Harness for callee-return. Loads the student's shared library, calls
 * solve(secret), and reports success only if `solve` returns the secret back
 * unchanged. The secret is a random 64-bit value passed as argv[2], so a
 * hardcoded `mov rax, N; ret` only "wins" with negligible probability.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)
#define SUCCESS_MARKER "callee-return-success\n"

static int write_all(int fd, const char *buf, size_t len) {
    while (len > 0) {
        ssize_t written = write(fd, buf, len);
        if (written < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        if (written == 0) {
            return -1;
        }
        buf += written;
        len -= written;
    }
    return 0;
}

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 3 && argc != 4) {
        fprintf(stderr, "usage: %s lib.so secret [success-fd]\n", argv[0]);
        return 2;
    }

    uint64_t secret = strtoull(argv[2], NULL, 0);
    int success_fd = argc == 4 ? atoi(argv[3]) : -1;

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    uint64_t (*solve)(uint64_t) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("found solve at %p", (void *)solve);
    LOG("calling solve(0x%lx) --- your code should return that value back unchanged in rax", secret);

    uint64_t got = solve(secret);

    LOG("solve() returned 0x%lx", got);
    if (got == secret) {
        LOG("match! return value == secret.");
        if (success_fd >= 0 && write_all(success_fd, SUCCESS_MARKER, sizeof(SUCCESS_MARKER) - 1) < 0) {
            LOG("failed to report success to checker");
            return 2;
        }
        return 0;
    }
    LOG("mismatch: you returned 0x%lx (%lu), but we sent in 0x%lx (%lu).",
        got, got, secret, secret);
    LOG("return the secret back, untouched!");
    return 1;
}
