.intel_syntax noprefix

.text
.global call_on_stack
.type call_on_stack, @function
call_on_stack:
    mov qword ptr [rip + saved_rsp_for_solve], rsp
    mov qword ptr [rip + saved_rbp_for_solve], rbp
    mov qword ptr [rip + saved_rbx_for_solve], rbx
    mov qword ptr [rip + saved_r12_for_solve], r12
    mov qword ptr [rip + saved_r13_for_solve], r13
    mov qword ptr [rip + saved_r14_for_solve], r14
    mov qword ptr [rip + saved_r15_for_solve], r15

    mov rsp, rsi
    call rdi
    mov rax, rsp

    mov rbp, qword ptr [rip + saved_rbp_for_solve]
    mov rbx, qword ptr [rip + saved_rbx_for_solve]
    mov r12, qword ptr [rip + saved_r12_for_solve]
    mov r13, qword ptr [rip + saved_r13_for_solve]
    mov r14, qword ptr [rip + saved_r14_for_solve]
    mov r15, qword ptr [rip + saved_r15_for_solve]
    mov rsp, qword ptr [rip + saved_rsp_for_solve]
    ret
.size call_on_stack, .-call_on_stack

.bss
.align 8
saved_rsp_for_solve:
    .quad 0
saved_rbp_for_solve:
    .quad 0
saved_rbx_for_solve:
    .quad 0
saved_r12_for_solve:
    .quad 0
saved_r13_for_solve:
    .quad 0
saved_r14_for_solve:
    .quad 0
saved_r15_for_solve:
    .quad 0

.section .note.GNU-stack,"",@progbits
