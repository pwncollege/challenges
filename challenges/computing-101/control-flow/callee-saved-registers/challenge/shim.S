/*
 * Asm support for callee-saved-registers.
 *
 * enter_solve seeds rbx,r12,r13,r14,r15 with the caller's sentinels, calls
 * solve, then snapshots those registers as solve left them. check_callee_clobbered
 * snapshots them as solve set them (expected: 0x1337) for the C checker.
 *
 * Shared state lives here in .bss so both this file and harness.c can reach it
 * without PIE/GOT gymnastics.
 */
.intel_syntax noprefix

.bss
.align 8
.global expected
expected:   .skip 40            /* 5 * 8: sentinels for rbx,r12,r13,r14,r15   */
.global seen
seen:       .skip 40            /* those registers as solve left them          */
.global seen2
seen2:      .skip 40            /* those registers as check_callee_clobbered saw */
.global clobber_ok
clobber_ok: .skip 4

.text

/*
 * void enter_solve(solve /rdi/, checkfn /rsi/)
 * Put the sentinels into the callee-saved registers, call solve(checkfn), then
 * record how solve left those registers. enter_solve itself preserves the
 * callee-saved registers for ITS caller (main).
 */
.global enter_solve
.type enter_solve, @function
enter_solve:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp
    mov  rbp, rsp
    lea  rax, [rip + expected]
    mov  rbx, [rax + 0x00]
    mov  r12, [rax + 0x08]
    mov  r13, [rax + 0x10]
    mov  r14, [rax + 0x18]
    mov  r15, [rax + 0x20]
    mov  rax, rdi               /* rax = solve */
    mov  rdi, rsi               /* rdi = checkfn (solve's argument) */
    and  rsp, -16               /* 16-byte align for the call */
    call rax                    /* solve(checkfn) */
    lea  rax, [rip + seen]      /* snapshot rbx,r12-r15 as solve left them */
    mov  [rax + 0x00], rbx
    mov  [rax + 0x08], r12
    mov  [rax + 0x10], r13
    mov  [rax + 0x18], r14
    mov  [rax + 0x20], r15
    mov  rsp, rbp
    pop  rbp
    pop  r15
    pop  r14
    pop  r13
    pop  r12
    pop  rbx
    ret
.size enter_solve, .-enter_solve

/*
 * void check_callee_clobbered(void)
 * Snapshot rbx,r12,r13,r14,r15 (the student should have set them to 0x1337),
 * then hand off to the C checker. Uses rax (caller-saved, not under test) as a
 * scratch base, so it leaves rbx,r12-r15 exactly as it found them.
 */
.global check_callee_clobbered
.type check_callee_clobbered, @function
check_callee_clobbered:
    lea  rax, [rip + seen2]
    mov  [rax + 0x00], rbx
    mov  [rax + 0x08], r12
    mov  [rax + 0x10], r13
    mov  [rax + 0x18], r14
    mov  [rax + 0x20], r15
    push rbp
    mov  rbp, rsp
    and  rsp, -16               /* align regardless of how solve called us */
    call check_clobber_c
    mov  rsp, rbp
    pop  rbp
    ret
.size check_callee_clobbered, .-check_callee_clobbered

.section .note.GNU-stack, "", @progbits
