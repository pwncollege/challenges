#!/usr/bin/env python3
import hashlib
import secrets
import subprocess
import tempfile
import textwrap
from pathlib import Path

BUFFER_SIZE = 256
FLAG_SIZE = 256
STACK_SIZE = BUFFER_SIZE + FLAG_SIZE
TOTAL_OPS = 1024  # per-program randomized add/sub ops
BLOB_SIZE = 65536
MSG_CORRECT = "✨ Correct: you checked it twice, and it shows!\n"
MSG_WRONG = "🚫 Wrong: Santa told you to check that list twice!\n"
MSG_CORRECT_LEN = len(MSG_CORRECT.encode("utf-8"))
MSG_WRONG_LEN = len(MSG_WRONG.encode("utf-8"))
NAMES_FILE = "nice.txt"
OUTPUT_DIR = Path("naughty-or-nice")
SOLUTION_DIR = Path("solution")
PREFIX = b"ADVENT-2025"


def generate_program(solution_bytes):
    msg_correct_esc = MSG_CORRECT.replace("\n", "\\n")
    msg_wrong_esc = MSG_WRONG.replace("\n", "\\n")
    rng = secrets.SystemRandom()

    final_bytes = list(solution_bytes)
    op_mask_offsets = {}
    op_value_offsets = {}
    broadcast_offsets = {}
    blob = [rng.randrange(256) for _ in range(BLOB_SIZE)]

    asm_parts = []
    asm_parts.append(
        textwrap.dedent(
            f"""
            .intel_syntax noprefix
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
        )
    )

    # Randomized vector add/subs, sometimes masked so only some lanes change.
    for op_index in range(TOTAL_OPS):
        block = rng.randrange(BUFFER_SIZE // 32)
        is_add = rng.getrandbits(1) == 1
        use_broadcast = rng.getrandbits(1) == 1
        if use_broadcast:
            offset_val = rng.randrange(BLOB_SIZE)
            broadcast_offsets[op_index] = offset_val
            value = blob[offset_val]
            lane_values = [value] * 32
        else:
            offset_val = rng.randrange(BLOB_SIZE - 32 + 1)
            op_value_offsets[op_index] = offset_val
            lane_values = blob[offset_val : offset_val + 32]
        use_mask = rng.random() < 0.10  # ~10% chance to blend with a lane mask
        mask = None
        if use_mask:
            while True:
                offset_mask = rng.randrange(BLOB_SIZE - 32 + 1)
                mask = blob[offset_mask : offset_mask + 32]
                if any(b & 0x80 for b in mask):
                    op_mask_offsets[op_index] = offset_mask
                    break
        base = block * 32
        for i in range(base, base + 32):
            if (not use_mask) or (mask[i - base] & 0x80):
                final_bytes[i] = (
                    (final_bytes[i] + lane_values[i - base]) & 0xFF
                    if is_add
                    else (final_bytes[i] - lane_values[i - base]) & 0xFF
                )
        offset = base - BUFFER_SIZE
        instr = "vpaddb" if is_add else "vpsubb"
        asm_block = [
            f"vmovdqu ymm0, [rbp{offset:+}]",
        ]
        if use_broadcast:
            asm_block.append(
                f"vpbroadcastb ymm1, byte ptr [rip+ro_blob+{broadcast_offsets[op_index]}]"
            )
        else:
            asm_block.append(
                f"vmovdqu ymm1, [rip+ro_blob+{op_value_offsets[op_index]}]"
            )
        asm_block.extend(
            [
            f"{instr} ymm2, ymm0, ymm1",
        ]
        )
        if use_mask:
            asm_block.extend(
                [
                    f"vmovdqu ymm3, [rip+ro_blob+{op_mask_offsets[op_index]}]",
                    "vpblendvb ymm0, ymm0, ymm2, ymm3",
                    f"vmovdqu [rbp{offset:+}], ymm0",
                ]
            )
        else:
            asm_block.append(f"vmovdqu [rbp{offset:+}], ymm2")

        asm_parts.append(
            textwrap.dedent(
                "\n                ".join([""] + asm_block + [""])
            )
        )

    for block in range(BUFFER_SIZE // 32):
        offset = block * 32 - BUFFER_SIZE
        asm_parts.append(
            textwrap.dedent(
                f"""
                vmovdqu ymm0, [rbp{offset:+}]
                vpcmpeqb ymm1, ymm0, [rip+final_block_{block}]
                vpmovmskb eax, ymm1
                cmp eax, -1
                jne wrong
                """
            )
        )

    asm_parts.append(
        textwrap.dedent(
            f"""
            # write CORRECT
            mov rax, 1
            mov rdi, 1
            lea rsi, [rip+msg_correct]
            mov rdx, {MSG_CORRECT_LEN}
            syscall
            # exit 0
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
        )
    )

    final_block_lines = []
    for block in range(BUFFER_SIZE // 32):
        start = block * 32
        final_block_lines.append(f"final_block_{block}:")
        block_bytes = final_bytes[start : start + 32]
        for i in range(0, 32, 16):
            chunk = block_bytes[i : i + 16]
            final_block_lines.append(
                "    .byte " + ", ".join(f"0x{b:02x}" for b in chunk)
            )

    def format_bytes(byte_list):
        return [
            "    .byte " + ", ".join(f"0x{b:02x}" for b in byte_list[i : i + 16])
            for i in range(0, len(byte_list), 16)
        ]

    blob_body = "\n".join(format_bytes(blob))
    blob_section = textwrap.dedent(
        f"""
            .p2align 6
        ro_blob:
        {blob_body}
        """
    )

    asm_parts.append(
        textwrap.dedent(
            f"""
            .section .rodata
            msg_correct: .asciz "{msg_correct_esc}"
            msg_wrong:   .asciz "{msg_wrong_esc}"
                .p2align 6
            finals:
            {'\n'.join(final_block_lines)}
            {blob_section}
                .p2align 6
            """
        )
    )

    return "\n".join(asm_parts)


def compile_binary(asm_path: Path, bin_path: Path):
    subprocess.run(
        [
            "gcc",
            "-nostdlib",
            "-static",
            "-O0",
            "-s",
            "-mavx2",
            str(asm_path),
            "-o",
            str(bin_path),
        ],
        check=True,
    )


def main():
    names = [
        line.rstrip("\n")
        for line in Path(NAMES_FILE).read_text().splitlines()
        if line.strip()
    ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SOLUTION_DIR.mkdir(parents=True, exist_ok=True)

    for name in names:
        digest = hashlib.sha256(PREFIX + name.encode("utf-8")).hexdigest()

        message = f"🎅 {name} is nice! 🎅\n".encode("utf-8")
        padded = message.ljust(BUFFER_SIZE, b"\x00")[:BUFFER_SIZE]
        final_bytes = list(padded)
        asm_text = generate_program(bytes(final_bytes))

        out_path = OUTPUT_DIR / digest
        with tempfile.TemporaryDirectory() as tmpdir:
            asm_path = Path(tmpdir) / "program.s"
            asm_path.write_text(asm_text)
            compile_binary(asm_path, out_path)
        out_path.chmod(0o4755)
        solution_path = SOLUTION_DIR / digest
        solution_path.write_bytes(message)


if __name__ == "__main__":
    main()
