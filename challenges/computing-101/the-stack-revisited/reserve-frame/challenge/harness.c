#define _GNU_SOURCE
#include <dlfcn.h>
#include <err.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

/*
 * Harness for reserve-frame. It calls
 *   void solve(void)
 * on a temporary stack whose would-be 256-byte frame has been filled with
 * nonzero marker bytes. A correct solve reserves that frame, clears it, restores
 * rsp, and returns. The flag never enters this unprivileged process.
 */

#define FRAME_LEN 256
#define STACK_LEN 16384
#define STACK_TOP_SLACK 128
#define MARKER 0xa5

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

uintptr_t call_on_stack(void (*solve)(void), void *stack_top);

int main(int argc, char **argv) {
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        errx(2, "usage: %s lib.so", argv[0]);
    }

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        errx(2, "dlopen failed: %s", dlerror());
    }
    LOG("resolving `solve` symbol ...");
    void (*solve)(void) = (void (*)(void))dlsym(h, "solve");
    if (!solve) {
        errx(2, "missing `solve` symbol --- did you `.global solve` in your assembly?");
    }

    unsigned char *stack = mmap(NULL, STACK_LEN, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (stack == MAP_FAILED) {
        err(2, "mmap");
    }

    uintptr_t stack_top = ((uintptr_t)stack + STACK_LEN - STACK_TOP_SLACK) & ~(uintptr_t)0xf;
    unsigned char *frame = (unsigned char *)(stack_top - 8 - FRAME_LEN);
    memset(frame, MARKER, FRAME_LEN);

    LOG("calling solve() on a temporary stack with 256 nonzero bytes where its frame will be");
    uintptr_t rsp_after = call_on_stack(solve, (void *)stack_top);
    if (rsp_after != stack_top) {
        LOG("solve returned with rsp changed by %+ld bytes", (long)(rsp_after - stack_top));
        return 1;
    }

    size_t bad = 0;
    size_t first_bad = 0;
    for (size_t i = 0; i < FRAME_LEN; i++) {
        if (frame[i] != 0) {
            if (bad == 0) {
                first_bad = i;
            }
            bad++;
        }
    }

    if (bad != 0) {
        LOG("%zu byte%s of the frame still nonzero; first one is [rsp+0x%zx] = 0x%02x",
            bad, bad == 1 ? "" : "s", first_bad, frame[first_bad]);
        return 1;
    }

    LOG("solve cleared the whole 256-byte frame and restored rsp");
    munmap(stack, STACK_LEN);
    return 0;
}
