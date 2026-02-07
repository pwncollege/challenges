#!/usr/bin/env python3
import secrets
import subprocess
import textwrap
import tempfile
import sys
from pathlib import Path

BUFFER_SIZE = 1024
FLAG_SIZE = 256
STACK_SIZE = BUFFER_SIZE + FLAG_SIZE
TOTAL_OPS = BUFFER_SIZE * BUFFER_SIZE
MSG_CORRECT = "✨ Correct: you checked it twice, and it shows!\n"
MSG_WRONG = "🚫 Wrong: Santa told you to check that list twice!\n"
MSG_CORRECT_LEN = len(MSG_CORRECT.encode("utf-8"))
MSG_WRONG_LEN = len(MSG_WRONG.encode("utf-8"))


def generate_program():
    rng = secrets.SystemRandom()
    initial_bytes = [rng.randrange(256) for _ in range(BUFFER_SIZE)]
    final_bytes = initial_bytes.copy()
    operations = []
    for _ in range(TOTAL_OPS):
        index = rng.randrange(BUFFER_SIZE)
        is_add = rng.getrandbits(1) == 1
        value = rng.randrange(1, 256)
        operations.append((index, is_add, value))
        final_bytes[index] = (final_bytes[index] + value) & 0xFF if is_add else (final_bytes[index] - value) & 0xFF
    return initial_bytes, final_bytes, operations


def write_assembly(final_bytes, operations):
    msg_correct_esc = MSG_CORRECT.replace("\n", "\\n")
    msg_wrong_esc = MSG_WRONG.replace("\n", "\\n")
    header = textwrap.dedent(
        f"""\
        .intel_syntax noprefix
        .section .rodata
        path_flag:   .asciz "/flag"
        msg_correct: .asciz "{msg_correct_esc}"
        msg_wrong:   .asciz "{msg_wrong_esc}"
        .text
        .globl _start
        _start:
            mov rbp, rsp
            sub rsp, {STACK_SIZE}
            mov eax, 0
            mov edi, 0
            lea rsi, [rbp-{BUFFER_SIZE}]
            mov edx, {BUFFER_SIZE}
            syscall
        """
    ).rstrip()

    body = []
    for index, is_add, value in operations:
        offset = index - BUFFER_SIZE
        instr = "add" if is_add else "sub"
        body.append(f"    {instr} byte ptr [rbp{offset:+}], {value}")

    compares = []
    for index, byte_val in enumerate(final_bytes):
        offset = index - BUFFER_SIZE
        compares.append(f"    cmp byte ptr [rbp{offset:+}], {byte_val}")
        compares.append("    jne wrong")

    footer = textwrap.dedent(
        f"""\
            # write CORRECT
            mov rax, 1
            mov rdi, 1
            lea rsi, [rip+msg_correct]
            mov rdx, {MSG_CORRECT_LEN}
            syscall
            # open /flag
            mov eax, 2
            lea rdi, [rip+path_flag]
            mov esi, 0
            mov edx, 0
            syscall
            cmp rax, 0
            jl clean_exit
            mov r12, rax          # save fd
            # read flag into lower part of stack
            mov eax, 0
            mov rdi, r12
            lea rsi, [rbp-{BUFFER_SIZE + FLAG_SIZE}]
            mov edx, {FLAG_SIZE}
            syscall
            cmp rax, 0
            jle clean_exit
            mov rcx, rax          # bytes read
            # write flag
            mov rax, 1
            mov rdi, 1
            lea rsi, [rbp-{BUFFER_SIZE + FLAG_SIZE}]
            mov rdx, rcx
            syscall
            cmp rax, 0
            jl clean_exit
            # exit 0
            mov eax, 60
            mov edi, 0
            syscall
        clean_exit:
            mov eax, 60
            mov edi, 0
            syscall
        wrong:
            mov rax, 1
            mov rdi, 1
            lea rsi, [rip+msg_wrong]
            mov rdx, {MSG_WRONG_LEN}
            syscall
            mov eax, 60
            mov edi, 1
            syscall
        """
    ).rstrip()

    asm = "\n".join([header, *body, *compares, footer, ""])
    return asm


def compile_binary(asm_path: Path, bin_path: Path):
    subprocess.run(
        ["gcc", "-nostdlib", "-static", "-O0", "-s", str(asm_path), "-o", str(bin_path)],
        check=True,
    )


def main():
    initial_bytes, final_bytes, operations = generate_program()
    asm_text = write_assembly(final_bytes, operations)
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_path = Path(tmpdir) / "program.s"
        bin_path = Path(tmpdir) / "program"
        asm_path.write_text(asm_text)
        compile_binary(asm_path, bin_path)
        sys.stdout.buffer.write(bin_path.read_bytes())


if __name__ == "__main__":
    main()
