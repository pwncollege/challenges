/*
 * load_secret is deliberately hand-written so the stale stack layout is exact.
 *
 * From solve's point of view after `call rdi` returns, the secret qword starts
 * at [rsp-0x10]: 8 bytes for the callback return address plus this 8-byte
 * frame.
 */
.intel_syntax noprefix
.text
.global load_secret
.type load_secret, @function
load_secret:
    mov dword ptr [rip + load_secret_ran], 1

    sub rsp, 0x8
    mov rax, qword ptr [rip + secret_value]
    mov qword ptr [rsp], rax

    xor eax, eax
    add rsp, 0x8
    ret
.size load_secret, .-load_secret

.section .note.GNU-stack,"",@progbits
