#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/random.h>
#include <unistd.h>

/*
 * Harness for callee-saved-registers.
 *
 * We call solve(check_callee_clobbered). Before the call, the asm shim
 * `enter_solve` seeds the callee-saved registers rbx, r12, r13, r14, r15 with
 * random sentinels --- these belong to us (solve's caller), and the ABI says
 * solve must hand them back unchanged.
 *
 *   - solve is expected to actually USE those registers (set them all to
 *     0x1337) and prove it by calling check_callee_clobbered, which verifies
 *     the 0x1337 values and records success.
 *   - solve must then restore rbx,r12-r15 before returning. After solve
 *     returns, enter_solve snapshots them into seen[], and we check they match
 *     the sentinels we put there.
 *
 * Shared state lives in shim.S (.bss); declared extern here.
 */

#define LOG(...) do { fprintf(stderr, "[harness] " __VA_ARGS__); fputc('\n', stderr); } while (0)

#define WORK_VALUE 0x1337

extern uint64_t expected[5];   /* sentinels placed in rbx,r12,r13,r14,r15        */
extern uint64_t seen[5];       /* those registers as solve left them (post-return)*/
extern uint64_t seen2[5];      /* those registers as check_callee_clobbered saw   */
extern int clobber_ok;         /* set when check_callee_clobbered saw all 0x1337  */

extern void enter_solve(void (*solve)(void (*)(void)), void (*checkfn)(void));
extern void check_callee_clobbered(void);

static char flagbuf[4096];
static size_t flaglen;
static const char *regname[5] = {"rbx", "r12", "r13", "r14", "r15"};

/* Called from check_callee_clobbered (asm) after it snapshots the registers. */
void __attribute__((force_align_arg_pointer)) check_clobber_c(void) {
    for (int i = 0; i < 5; i++) {
        if (seen2[i] != WORK_VALUE) {
            printf("when you called check_callee_clobbered, %s held 0x%lx, not 0x%x --- "
                   "put your work (0x%x) in all of rbx,r12,r13,r14,r15 first.\n",
                   regname[i], seen2[i], WORK_VALUE, WORK_VALUE);
            return;
        }
    }
    clobber_ok = 1;
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
    void (*solve)(void (*)(void)) = dlsym(h, "solve");
    if (!solve) {
        LOG("missing `solve` symbol --- did you `.global solve` in your assembly?");
        return 2;
    }

    LOG("calling solve(check_callee_clobbered):");
    LOG("  rdi = check_callee_clobbered (confirms you put 0x%x in rbx,r12,r13,r14,r15)", WORK_VALUE);
    LOG("  rbx,r12,r13,r14,r15 arrive holding MY values --- give them back unchanged");

    enter_solve(solve, check_callee_clobbered);

    if (!clobber_ok) {
        LOG("solve never set rbx,r12-r15 to 0x%x and called check_callee_clobbered.", WORK_VALUE);
        return 1;
    }
    for (int i = 0; i < 5; i++) {
        if (seen[i] != expected[i]) {
            LOG("you didn't restore %s: it should be 0x%lx, but solve left it 0x%lx.",
                regname[i], expected[i], seen[i]);
            return 1;
        }
    }
    fwrite(flagbuf, 1, flaglen, stdout);
    LOG("callee-saved registers restored --- flag released.");
    return 0;
}
