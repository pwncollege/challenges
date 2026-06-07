/*
 * Asm support for atoi-two-digits. Both of the student's functions (atoi_digit
 * and atoi) are real functions the grader calls, so each must honor the calling
 * convention: leave the callee-saved registers (rbx, r12-r15) exactly as found.
 *
 * call_fn seeds those registers with sentinels, calls fn(s), and records what
 * fn left in them (in cc_seen) so the C harness can check.
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

/* long call_fn(long (*fn)(const char *) /rdi/, const char *s /rsi/) */
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
    mov  rdi, rsi               /* rdi = s (its argument) */
    mov  rbx, 0x1111111111111111
    mov  r12, 0x1212121212121212
    mov  r13, 0x1313131313131313
    mov  r14, 0x1414141414141414
    mov  r15, 0x1515151515151515
    and  rsp, -16               /* 16-byte align for the call */
    call rax                    /* fn(s); return value stays in rax */
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

.section .note.GNU-stack, "", @progbits
