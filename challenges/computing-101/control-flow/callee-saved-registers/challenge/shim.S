/*
 * Asm support for callee-saved-registers.
 *
 * enter_solve seeds rbx,rbp,r12-r15 with the caller's sentinels, calls solve,
 * then snapshots those registers and the actual post-return rsp before safely
 * restoring its private stack. check_callee_clobbered snapshots the same six
 * registers while solve is borrowing them (expected: 0x1337).
 *
 * Shared state lives here in .bss so both this file and harness.c can reach it
 * without PIE/GOT gymnastics.
 */
.intel_syntax noprefix

.bss
.align 8
.global expected
expected:       .skip 48       /* sentinels for rbx,rbp,r12,r13,r14,r15 */
.global seen
seen:           .skip 48       /* those registers as solve left them */
.global seen2
seen2:          .skip 48       /* values check_callee_clobbered saw */
.global incoming
incoming:       .skip 64       /* randomized unspecified caller-saved inputs */
.global expected_rsp
expected_rsp:   .skip 8        /* rsp immediately before the call */
.global seen_rsp
seen_rsp:       .skip 8        /* actual rsp immediately after solve returned */
restore_rsp:    .skip 8        /* private recovery stack; never trusted to solve */
solve_fn:       .skip 8
check_fn:       .skip 8
.global clobber_ok
clobber_ok:     .skip 4

.text

/*
 * void enter_solve(solve /rdi/, checkfn /rsi/)
 * Put the sentinels into the callee-saved registers, call solve(checkfn), then
 * record how solve left those registers and rsp. enter_solve itself preserves
 * the callee-saved registers for its caller (main).
 */
.global enter_solve
.type enter_solve, @function
enter_solve:
    push rbx
    push rbp
    push r12
    push r13
    push r14
    push r15
    mov  qword ptr [rip + restore_rsp], rsp
    mov  qword ptr [rip + solve_fn], rdi
    mov  qword ptr [rip + check_fn], rsi

    lea  rax, [rip + expected]
    mov  rbx, qword ptr [rax + 0x00]
    mov  rbp, qword ptr [rax + 0x08]
    mov  r12, qword ptr [rax + 0x10]
    mov  r13, qword ptr [rax + 0x18]
    mov  r14, qword ptr [rax + 0x20]
    mov  r15, qword ptr [rax + 0x28]
    and  rsp, -16
    mov  qword ptr [rip + expected_rsp], rsp

    mov  rdi, qword ptr [rip + check_fn]
    mov  rax, qword ptr [rip + incoming + 0x00]
    mov  rcx, qword ptr [rip + incoming + 0x08]
    mov  rdx, qword ptr [rip + incoming + 0x10]
    mov  rsi, qword ptr [rip + incoming + 0x18]
    mov  r8,  qword ptr [rip + incoming + 0x20]
    mov  r9,  qword ptr [rip + incoming + 0x28]
    mov  r10, qword ptr [rip + incoming + 0x30]
    mov  r11, qword ptr [rip + incoming + 0x38]
    call qword ptr [rip + solve_fn]

    /* Do not use the returned stack until after recording and replacing it. */
    mov  qword ptr [rip + seen_rsp], rsp
    mov  qword ptr [rip + seen + 0x00], rbx
    mov  qword ptr [rip + seen + 0x08], rbp
    mov  qword ptr [rip + seen + 0x10], r12
    mov  qword ptr [rip + seen + 0x18], r13
    mov  qword ptr [rip + seen + 0x20], r14
    mov  qword ptr [rip + seen + 0x28], r15
    mov  rsp, qword ptr [rip + restore_rsp]
    pop  r15
    pop  r14
    pop  r13
    pop  r12
    pop  rbp
    pop  rbx
    ret
.size enter_solve, .-enter_solve

/*
 * void check_callee_clobbered(void)
 * Snapshot rbx,rbp,r12-r15 (the student should have set them to 0x1337), then
 * hand off to the C checker. It restores every callee-saved register it uses.
 */
.global check_callee_clobbered
.type check_callee_clobbered, @function
check_callee_clobbered:
    mov  qword ptr [rip + seen2 + 0x00], rbx
    mov  qword ptr [rip + seen2 + 0x08], rbp
    mov  qword ptr [rip + seen2 + 0x10], r12
    mov  qword ptr [rip + seen2 + 0x18], r13
    mov  qword ptr [rip + seen2 + 0x20], r14
    mov  qword ptr [rip + seen2 + 0x28], r15
    push rbp
    mov  rbp, rsp
    and  rsp, -16
    call check_clobber_c
    mov  rsp, rbp
    pop  rbp
    ret
.size check_callee_clobbered, .-check_callee_clobbered

.section .note.GNU-stack, "", @progbits
