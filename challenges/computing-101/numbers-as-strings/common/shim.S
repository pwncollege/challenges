/*
 * Asm support for the numbers-as-strings levels. The student's function is a
 * real function the grader calls, so it must honor the calling convention:
 * leave the callee-saved registers (rbx, rbp, r12-r15) and rsp as found.
 *
 * call_fn and call_fn2 seed the callee-saved registers with sentinels and the
 * unspecified caller-saved registers with values supplied by the C harness.
 * After the student's function returns, they snapshot the callee-saved
 * registers and the actual rsp before restoring the harness's own stack.
 *
 * Shared state lives here in .bss so both this file and harness.c can reach it
 * without PIE/GOT gymnastics.
 */
.intel_syntax noprefix

.bss
.align 8
.global cc_seen
cc_seen:        .skip 48       /* rbx, rbp, r12, r13, r14, r15 as fn left them */
.global cc_incoming
cc_incoming:    .skip 64       /* randomized unspecified caller-saved inputs */
.global cc_expected_rsp
cc_expected_rsp: .skip 8       /* rsp immediately before the call */
.global cc_seen_rsp
cc_seen_rsp:    .skip 8        /* actual rsp immediately after fn returned */
cc_restore_rsp: .skip 8        /* private recovery stack; never trusted to fn */
cc_fn:          .skip 8
cc_arg1:        .skip 8
cc_arg2:        .skip 8
cc_result:      .skip 8

.text

.macro save_harness_state
    push rbx
    push rbp
    push r12
    push r13
    push r14
    push r15
    mov  qword ptr [rip + cc_restore_rsp], rsp
.endm

.macro seed_callee_saved
    mov  rbx, 0x1111111111111111
    mov  rbp, 0xb0b0b0b0b0b0b0b0
    mov  r12, 0x1212121212121212
    mov  r13, 0x1313131313131313
    mov  r14, 0x1414141414141414
    mov  r15, 0x1515151515151515
.endm

.macro snapshot_and_restore
    /* Do not use the returned stack until after recording and replacing it. */
    mov  qword ptr [rip + cc_seen_rsp], rsp
    mov  qword ptr [rip + cc_result], rax
    mov  qword ptr [rip + cc_seen + 0x00], rbx
    mov  qword ptr [rip + cc_seen + 0x08], rbp
    mov  qword ptr [rip + cc_seen + 0x10], r12
    mov  qword ptr [rip + cc_seen + 0x18], r13
    mov  qword ptr [rip + cc_seen + 0x20], r14
    mov  qword ptr [rip + cc_seen + 0x28], r15
    mov  rsp, qword ptr [rip + cc_restore_rsp]
    pop  r15
    pop  r14
    pop  r13
    pop  r12
    pop  rbp
    pop  rbx
    mov  rax, qword ptr [rip + cc_result]
    ret
.endm

/* long call_fn(fn /rdi/, arg /rsi/) -> fn(arg); arg may be a pointer or a value */
.global call_fn
.type call_fn, @function
call_fn:
    save_harness_state
    mov  qword ptr [rip + cc_fn], rdi
    mov  qword ptr [rip + cc_arg1], rsi
    seed_callee_saved
    and  rsp, -16
    mov  qword ptr [rip + cc_expected_rsp], rsp

    mov  rdi, qword ptr [rip + cc_arg1]
    mov  rax, qword ptr [rip + cc_incoming + 0x00]
    mov  rcx, qword ptr [rip + cc_incoming + 0x08]
    mov  rdx, qword ptr [rip + cc_incoming + 0x10]
    mov  rsi, qword ptr [rip + cc_incoming + 0x18]
    mov  r8,  qword ptr [rip + cc_incoming + 0x20]
    mov  r9,  qword ptr [rip + cc_incoming + 0x28]
    mov  r10, qword ptr [rip + cc_incoming + 0x30]
    mov  r11, qword ptr [rip + cc_incoming + 0x38]
    call qword ptr [rip + cc_fn]
    snapshot_and_restore
.size call_fn, .-call_fn

/* long call_fn2(fn /rdi/, arg1 /rsi/, arg2 /rdx/) -> fn(arg1, arg2) */
.global call_fn2
.type call_fn2, @function
call_fn2:
    save_harness_state
    mov  qword ptr [rip + cc_fn], rdi
    mov  qword ptr [rip + cc_arg1], rsi
    mov  qword ptr [rip + cc_arg2], rdx
    seed_callee_saved
    and  rsp, -16
    mov  qword ptr [rip + cc_expected_rsp], rsp

    mov  rdi, qword ptr [rip + cc_arg1]
    mov  rsi, qword ptr [rip + cc_arg2]
    mov  rax, qword ptr [rip + cc_incoming + 0x00]
    mov  rcx, qword ptr [rip + cc_incoming + 0x08]
    mov  rdx, qword ptr [rip + cc_incoming + 0x10]
    mov  r8,  qword ptr [rip + cc_incoming + 0x20]
    mov  r9,  qword ptr [rip + cc_incoming + 0x28]
    mov  r10, qword ptr [rip + cc_incoming + 0x30]
    mov  r11, qword ptr [rip + cc_incoming + 0x38]
    call qword ptr [rip + cc_fn]
    snapshot_and_restore
.size call_fn2, .-call_fn2

.section .note.GNU-stack, "", @progbits
