/*
 * read_flag is deliberately hand-written so the stale stack layout is exact.
 *
 * From solve's point of view after `call rdi` returns, the copied flag starts
 * at [rsp-0x88]: 8 bytes for the callback return address plus this 128-byte
 * frame.
 */
.intel_syntax noprefix
.text
.global read_flag
.type read_flag, @function
read_flag:
    mov dword ptr [rip + read_flag_ran], 1

    sub rsp, 0x80
    lea rsi, [rip + flag_buf]
    mov rdi, rsp
    mov rcx, 16
    rep movsq

    xor eax, eax
    add rsp, 0x80
    ret
.size read_flag, .-read_flag

.section .note.GNU-stack,"",@progbits
