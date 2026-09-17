#define _GNU_SOURCE
#include <assert.h>
#include <err.h>

#include <checkpoint.h>

static volatile int initialized = 17;
static volatile int zeroed;

int main(void)
{
    long generation, value;
    /* Keep r12 inside one assembly block so C cannot spill and reload it. */
    asm volatile(
        ".intel_syntax noprefix\n\t"
        "mov r12, 42\n\t"
        "mov eax, %c[checkpoint]\n\t"
        "syscall\n\t"
        "test rax, rax\n\t"
        "jnz 1f\n\t"
        "mov r12, 99\n\t"
        "mov eax, %c[restore]\n\t"
        "syscall\n\t"
        "ud2\n\t"
        "1: mov rdx, r12\n\t"
        ".att_syntax prefix"
        : "=a" (generation), "=d" (value)
        : [checkpoint] "i" (SYS_checkpoint), [restore] "i" (SYS_restore)
        : "rcx", "r11", "r12", "memory", "cc");
    assert(generation == 1 && value == 42);

    volatile int local = 42;
    pid_t pid = getpid(), tid = gettid();

    generation = checkpoint();
    assert(generation >= 0 && generation <= 3);
    assert(getpid() == pid && gettid() == tid);
    assert(local == 42 && initialized == 17 && zeroed == 0);
    if (generation < 3) {
        local = -1;
        initialized = -2;
        zeroed = -3;
        restore();
        errx(1, "restore returned to its caller");
    }

    local = 99;
    initialized = 34;
    generation = checkpoint();
    assert(generation >= 0 && generation <= 1);
    assert(local == 99 && initialized == 34);
    if (generation == 0) {
        local = -1;
        initialized = -2;
        restore();
        errx(1, "restore returned to its caller");
    }
    return 0;
}
