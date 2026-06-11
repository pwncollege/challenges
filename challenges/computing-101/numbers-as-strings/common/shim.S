/*
 * Asm support for the numbers-as-strings levels. The student's function is a
 * real function the grader calls, so it must honor the calling convention:
 * leave the callee-saved registers (rbx, r12-r15) exactly as found.
 *
 * call_fn and call_fn2 seed those registers with sentinels, call fn with one
 * or two arguments, and record what fn left in them (in cc_seen) so the C
 * harness can check.
 *
 * cc_seen lives here in .bss so both this file and harness.c can reach it
 * without PIE/GOT gymnastics.
 */
.intel_syntax noprefix

.bss
.align 8
.global cc_seen
cc_seen: .skip 40               /* rbx, r12, r13, r14, r15 as fn left them */

.text

/* long call_fn(fn /rdi/, arg /rsi/) -> fn(arg); arg may be a pointer or a value */
.global call_fn
.type call_fn, @function
call_fn:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp
    mov  rbp, rsp
    mov  rax, rdi               /* rax = fn */
    mov  rdi, rsi               /* rdi = fn's argument */
    mov  rbx, 0x1111111111111111
    mov  r12, 0x1212121212121212
    mov  r13, 0x1313131313131313
    mov  r14, 0x1414141414141414
    mov  r15, 0x1515151515151515
    and  rsp, -16               /* 16-byte align for the call */
    call rax                    /* fn(arg); return value stays in rax */
    lea  rcx, [rip + cc_seen]   /* rcx is caller-saved --- safe scratch here */
    mov  [rcx + 0x00], rbx
    mov  [rcx + 0x08], r12
    mov  [rcx + 0x10], r13
    mov  [rcx + 0x18], r14
    mov  [rcx + 0x20], r15
    mov  rsp, rbp
    pop  rbp
    pop  r15
    pop  r14
    pop  r13
    pop  r12
    pop  rbx
    ret
.size call_fn, .-call_fn

/* long call_fn2(fn /rdi/, arg1 /rsi/, arg2 /rdx/) -> fn(arg1, arg2) */
.global call_fn2
.type call_fn2, @function
call_fn2:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp
    mov  rbp, rsp
    mov  rax, rdi               /* rax = fn */
    mov  rdi, rsi               /* rdi = arg1 */
    mov  rsi, rdx               /* rsi = arg2 */
    mov  rbx, 0x1111111111111111
    mov  r12, 0x1212121212121212
    mov  r13, 0x1313131313131313
    mov  r14, 0x1414141414141414
    mov  r15, 0x1515151515151515
    and  rsp, -16               /* 16-byte align for the call */
    call rax                    /* fn(arg1, arg2); return value stays in rax */
    lea  rcx, [rip + cc_seen]   /* rcx is caller-saved --- safe scratch here */
    mov  [rcx + 0x00], rbx
    mov  [rcx + 0x08], r12
    mov  [rcx + 0x10], r13
    mov  [rcx + 0x18], r14
    mov  [rcx + 0x20], r15
    mov  rsp, rbp
    pop  rbp
    pop  r15
    pop  r14
    pop  r13
    pop  r12
    pop  rbx
    ret
.size call_fn2, .-call_fn2

.section .note.GNU-stack, "", @progbits
