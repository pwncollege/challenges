#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * Harness for stale-stack-value. The student's solve(load_secret) receives a
 * function pointer. load_secret copies one qword into its own stack frame and
 * returns, leaving a stale value for solve to load and return.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)
#define SUCCESS_MARKER "stale-stack-value-success\n"

uint64_t secret_value;
int load_secret_ran = 0;

extern uint64_t load_secret(void);

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

static void read_exact_secret(void) {
    unsigned char *p = (unsigned char *)&secret_value;
    size_t got = 0;
    while (got < sizeof secret_value) {
        ssize_t n = read(0, p + got, sizeof secret_value - got);
        if (n < 0) {
            err(2, "read secret");
        }
        if (n == 0) {
            errx(2, "short secret read (%zu of %zu bytes)", got, sizeof secret_value);
        }
        got += n;
    }
    close(0);
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2 && argc != 3) {
        errx(2, "usage: %s lib.so [success-fd]", argv[0]);
    }

    int success_fd = argc == 3 ? atoi(argv[2]) : -1;
    read_exact_secret();

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        errx(2, "dlopen failed: %s", dlerror());
    }
    LOG("resolving `solve` symbol ...");
    uint64_t (*solve)(uint64_t (*)(void)) = (uint64_t (*)(uint64_t (*)(void)))dlsym(h, "solve");
    if (!solve) {
        errx(2, "missing `solve` symbol --- did you `.global solve` in your assembly?");
    }

    LOG("calling solve(load_secret) --- your code receives the load_secret function pointer in rdi");
    LOG("load_secret returns 0, but leaves an 8-byte stale value at [rsp-0x10] from solve's view");
    LOG("call load_secret, then return qword ptr [rsp-0x10] in rax:");

    uint64_t got = solve(load_secret);

    if (!load_secret_ran) {
        LOG("your solve returned without calling load_secret");
        return 1;
    }
    if (got != secret_value) {
        LOG("your solve returned 0x%lx, but the stale value was 0x%lx", got, secret_value);
        return 1;
    }

    LOG("match! return value == stale secret.");
    if (success_fd >= 0 && write_all(success_fd, SUCCESS_MARKER, sizeof(SUCCESS_MARKER) - 1) < 0) {
        LOG("failed to report success to checker");
        return 2;
    }
    return 0;
}
