#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/random.h>
#include <unistd.h>

/*
 * Harness for caller-saved-registers.
 *
 * We call solve(clobber_function, flag_function). Before the call, the asm shim
 * `enter_solve` seeds the seven caller-saved registers that aren't carrying an
 * argument (rax, rcx, rdx, r8, r9, r10, r11) with random sentinel values.
 *
 *   - clobber_function overwrites every caller-saved register (exactly what the
 *     ABI permits a callee to do) and records that it ran.
 *   - flag_function snapshots those seven registers on entry and hands them to
 *     flag_check, which prints the flag only if all of them still hold their
 *     sentinels (i.e. solve saved/restored them around the clobber call).
 *
 * The shared state below lives in shim.S (.bss) so the asm can touch it without
 * any PIE/GOT juggling; here we just declare it extern.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

extern uint64_t expected[7];   /* sentinels placed in rax,rcx,rdx,r8,r9,r10,r11 */
extern uint64_t seen[7];       /* what flag_function observed in those registers */
extern int clobber_called;     /* set by clobber_function */
extern int flag_shown;         /* set by flag_check once it releases the flag   */

extern void enter_solve(void (*solve)(void (*)(void), void (*)(void)),
                        void (*clobber)(void), void (*flagfn)(void));
extern void clobber_function(void);
extern void flag_function(void);

static char flagbuf[4096];
static size_t flaglen;
static const char *regname[7] = {"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"};

/* Called from flag_function (asm) after it snapshots the registers into seen[]. */
void __attribute__((force_align_arg_pointer)) flag_check(void) {
    if (!clobber_called) {
        printf("flag_function ran, but you never called clobber_function (rdi). "
               "Call it first --- that's the whole point.\n");
        return;
    }
    for (int i = 0; i < 7; i++) {
        if (seen[i] != expected[i]) {
            printf("register %s was not preserved across the call to clobber_function: "
                   "it held 0x%lx going in, but flag_function saw 0x%lx.\n",
                   regname[i], expected[i], seen[i]);
            return;
        }
    }
    flag_shown = 1;
    fwrite(flagbuf, 1, flaglen, stdout);
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    if (argc != 2) {
        fprintf(stderr, "usage: %s lib.so   (the flag is read from stdin)\n", argv[0]);
        return 2;
    }

    /* Receive the flag on stdin, not argv: argv is world-readable via
     * /proc/self/cmdline, which would let a solve dump the flag without doing
     * the register work. Consume it now so a solve that read()s fd 0 gets nothing. */
    ssize_t n;
    while (flaglen < sizeof flagbuf && (n = read(0, flagbuf + flaglen, sizeof flagbuf - flaglen)) > 0)
        flaglen += n;

    if (getrandom(expected, sizeof expected, 0) != (ssize_t)sizeof expected) {
        LOG("getrandom failed");
        return 2;
    }

    LOG("loading shared library %s ...", argv[1]);
    void *h = dlopen(argv[1], RTLD_NOW);
    if (!h) {
        LOG("dlopen failed: %s", dlerror());
        return 2;
    }
    LOG("resolving `solve` symbol ...");
    void (*solve)(void (*)(void), void (*)(void)) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }

    LOG("calling solve(clobber_function, flag_function):");
    LOG("  rdi = clobber_function  (overwrites every caller-saved register, as a callee may)");
    LOG("  rsi = flag_function     (prints the flag IF the caller-saved registers survived)");
    LOG("  rax,rcx,rdx,r8,r9,r10,r11 hold live values you must preserve across the clobber call");

    enter_solve(solve, clobber_function, flag_function);

    if (!clobber_called) {
        LOG("solve returned without ever calling clobber_function.");
        return 1;
    }
    if (!flag_shown) {
        LOG("solve finished, but the flag stayed locked (see the message above).");
        return 1;
    }
    LOG("the caller-saved registers survived --- nicely done.");
    return 0;
}
