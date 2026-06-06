/*
 * Asm support for caller-saved-registers.
 *
 * C cannot place specific values into rax/rcx/rdx/r8-r11 right at a call site,
 * so this shim does it. It also provides clobber_function (trashes all
 * caller-saved registers) and flag_function (snapshots them for the C checker).
 *
 * Shared state lives here in .bss so both this file and harness.c can reach it
 * without PIE/GOT gymnastics.
 */
.intel_syntax noprefix

.bss
.align 8
.global expected
expected:       .skip 56        /* 7 * 8 bytes: sentinels for rax,rcx,rdx,r8,r9,r10,r11 */
.global seen
seen:           .skip 56        /* what flag_function saw */
.global clobber_called
clobber_called: .skip 4
.global flag_shown
flag_shown:     .skip 4

.text

/*
 * void enter_solve(solve /rdi/, clobber /rsi/, flagfn /rdx/)
 * Seed the caller-saved registers with the sentinels, set up solve's two
 * arguments (rdi=clobber, rsi=flagfn), and call solve.
 */
.global enter_solve
.type enter_solve, @function
enter_solve:
    push rbx
    push rbp
    mov  rbp, rsp
    mov  rbx, rdi               /* stash solve in a callee-saved reg */
    mov  rdi, rsi               /* rdi = clobber  (solve's 1st arg)   */
    mov  rsi, rdx               /* rsi = flagfn   (solve's 2nd arg)   */
    lea  r11, [rip + expected]
    mov  rax, [r11 + 0x00]
    mov  rcx, [r11 + 0x08]
    mov  rdx, [r11 + 0x10]
    mov  r8,  [r11 + 0x18]
    mov  r9,  [r11 + 0x20]
    mov  r10, [r11 + 0x28]
    mov  r11, [r11 + 0x30]      /* load r11 last: it was the base pointer */
    and  rsp, -16               /* 16-byte align for the call */
    call rbx                    /* solve(clobber, flagfn) */
    mov  rsp, rbp
    pop  rbp
    pop  rbx
    ret
.size enter_solve, .-enter_solve

/*
 * void clobber_function(void)
 * Overwrite every caller-saved register, as a callee is permitted to, and note
 * that we ran. Leaves callee-saved registers untouched.
 */
.global clobber_function
.type clobber_function, @function
clobber_function:
    mov rax, 0xBAD0BAD0BAD0BAD0
    mov rcx, rax
    mov rdx, rax
    mov rsi, rax
    mov rdi, rax
    mov r8,  rax
    mov r9,  rax
    mov r10, rax
    mov r11, rax
    mov dword ptr [rip + clobber_called], 1
    ret
.size clobber_function, .-clobber_function

/*
 * void flag_function(void)
 * Snapshot the seven caller-saved registers on entry, then hand off to the C
 * checker. Uses rbx as a scratch base (saved/restored) so the snapshot doesn't
 * disturb any of the registers it is recording.
 */
.global flag_function
.type flag_function, @function
flag_function:
    push rbx
    lea  rbx, [rip + seen]
    mov  [rbx + 0x00], rax
    mov  [rbx + 0x08], rcx
    mov  [rbx + 0x10], rdx
    mov  [rbx + 0x18], r8
    mov  [rbx + 0x20], r9
    mov  [rbx + 0x28], r10
    mov  [rbx + 0x30], r11
    push rbp
    mov  rbp, rsp
    and  rsp, -16               /* align regardless of how solve called us */
    call flag_check
    mov  rsp, rbp
    pop  rbp
    pop  rbx
    ret
.size flag_function, .-flag_function

.section .note.GNU-stack, "", @progbits
