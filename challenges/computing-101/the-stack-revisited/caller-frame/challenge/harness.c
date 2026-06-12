#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

// Fixed-size flag field, big enough for any real flag (flags vary in length --
// do not assume the current length). Keep in sync with FLAG_BUF_LEN in
// .py/chal.py and the copy count in caller.S.
#define FLAG_LEN 128

extern void caller(void (*solve)(void), const char *flag_buf);

int main(int argc, char **argv) {
    // Unbuffer both streams so the [harness] narration and the solve's own
    // writes appear in real chronological order, even when stdout/stderr are
    // pipes rather than a tty.
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so\n", argv[0]);
        return 2;
    }

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    void (*solve)(void) = (void (*)(void))dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }
    LOG("found solve at %p", (void *)solve);

    LOG("reading %d bytes of flag from stdin ...", FLAG_LEN);
    char flag_buf[FLAG_LEN];
    ssize_t got = 0;
    while (got < FLAG_LEN) {
        ssize_t n = read(0, flag_buf + got, FLAG_LEN - got);
        if (n <= 0) {
            LOG("short flag read (%zd of %d bytes)", got, FLAG_LEN);
            return 2;
        }
        got += n;
    }

    LOG("calling caller(solve, flag_buf) --- caller stashes the flag in its local frame at [rsp+0x40] (from solve's view) and then calls into your solve");
    LOG("your `solve` should `write` %d bytes from [rsp+0x40] to stdout:", FLAG_LEN);

    caller(solve, flag_buf);

    LOG("caller() returned after your solve ran.");
    return 0;
}
