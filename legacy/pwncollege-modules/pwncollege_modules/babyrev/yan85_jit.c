#include <stdarg.h>

{% if walkthrough %}
{% include "disassemble.c" %}
{% endif %}


#define EMIT(where, type, v) { *(type*)where = (type)v; where = (type*)where+1; }
#define EQ(v) { EMIT(where, unsigned long long, v) }
#define ED(v) { EMIT(where, unsigned int, v) }
#define EB(v) { EMIT(where, unsigned char, v) }
#define EB2(v1, v2) { EB(v1) EB(v2) }
#define EB3(v1, v2, v3) { EB(v1) EB(v2) EB(v3) }
#define EB4(v1, v2, v3, v4) { EB(v1) EB(v2) EB(v3) EB(v4) }

void *helper_store_mem(vmstate_t *state, void *where, word_t reg_spec)
{
	// emits a mov [r8+memory], reg
	EB2(0x48, 0xb8); EQ(state->memory); // mov rax, state->memory
	EB3(0x49, 0x01, 0xc0); // add r8, rax
	if      (reg_spec == SPEC_REG_I) { EB3(0x4d, 0x89, 0x08); }
	else if (reg_spec == SPEC_REG_A) { EB3(0x4d, 0x89, 0x10); }
	else if (reg_spec == SPEC_REG_B) { EB3(0x4d, 0x89, 0x18); }
	else if (reg_spec == SPEC_REG_C) { EB3(0x4d, 0x89, 0x20); }
	else if (reg_spec == SPEC_REG_D) { EB3(0x4d, 0x89, 0x28); }
	else if (reg_spec == SPEC_REG_S) { EB3(0x4d, 0x89, 0x30); }
	else if (reg_spec == SPEC_REG_F) { EB3(0x4d, 0x89, 0x38); }
	else crash(state, "Unknown register in helper_store");
	return where;
}

void *helper_load_mem(vmstate_t *state, void *where, word_t reg_spec)
{
	// emits a mov reg, [r8]
	EB2(0x48, 0xb8); EQ(state->memory); // mov rax, state->memory
	EB3(0x49, 0x01, 0xc0); // add r8, rax
	if      (reg_spec == SPEC_REG_I) { EB3(0x4d, 0x8b, 0x08); }
	else if (reg_spec == SPEC_REG_A) { EB3(0x4d, 0x8b, 0x10); }
	else if (reg_spec == SPEC_REG_B) { EB3(0x4d, 0x8b, 0x18); }
	else if (reg_spec == SPEC_REG_C) { EB3(0x4d, 0x8b, 0x20); }
	else if (reg_spec == SPEC_REG_D) { EB3(0x4d, 0x8b, 0x28); }
	else if (reg_spec == SPEC_REG_S) { EB3(0x4d, 0x8b, 0x30); }
	else if (reg_spec == SPEC_REG_F) { EB3(0x4d, 0x8b, 0x38); }
	else crash(state, "Unknown register in helper_load");
	return where;
}

void *helper_combo_byte(vmstate_t *state, void *where, word_t reg1, word_t reg2)
{
	if      (reg1 == SPEC_REG_A && reg2 == SPEC_REG_A) { EB(0xd2); }
	else if (reg1 == SPEC_REG_A && reg2 == SPEC_REG_B) { EB(0xda); }
	else if (reg1 == SPEC_REG_A && reg2 == SPEC_REG_C) { EB(0xe2); }
	else if (reg1 == SPEC_REG_A && reg2 == SPEC_REG_D) { EB(0xea); }
	else if (reg1 == SPEC_REG_A && reg2 == SPEC_REG_F) { EB(0xfa); }
	else if (reg1 == SPEC_REG_A && reg2 == SPEC_REG_I) { EB(0xca); }
	else if (reg1 == SPEC_REG_A && reg2 == SPEC_REG_S) { EB(0xf2); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_A) { EB(0xd3); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_B) { EB(0xdb); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_C) { EB(0xe3); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_D) { EB(0xeb); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_F) { EB(0xfb); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_I) { EB(0xcb); }
	else if (reg1 == SPEC_REG_B && reg2 == SPEC_REG_S) { EB(0xf3); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_A) { EB(0xd4); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_B) { EB(0xdc); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_C) { EB(0xe4); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_D) { EB(0xec); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_F) { EB(0xfc); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_I) { EB(0xcc); }
	else if (reg1 == SPEC_REG_C && reg2 == SPEC_REG_S) { EB(0xf4); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_A) { EB(0xd5); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_B) { EB(0xdd); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_C) { EB(0xe5); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_D) { EB(0xed); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_F) { EB(0xfd); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_I) { EB(0xcd); }
	else if (reg1 == SPEC_REG_D && reg2 == SPEC_REG_S) { EB(0xf5); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_A) { EB(0xd7); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_B) { EB(0xdf); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_C) { EB(0xe7); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_D) { EB(0xef); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_F) { EB(0xff); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_I) { EB(0xcf); }
	else if (reg1 == SPEC_REG_F && reg2 == SPEC_REG_S) { EB(0xf7); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_A) { EB(0xd1); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_B) { EB(0xd9); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_C) { EB(0xe1); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_D) { EB(0xe9); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_F) { EB(0xf9); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_I) { EB(0xc9); }
	else if (reg1 == SPEC_REG_I && reg2 == SPEC_REG_S) { EB(0xf1); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_A) { EB(0xd6); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_B) { EB(0xde); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_C) { EB(0xe6); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_D) { EB(0xee); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_F) { EB(0xfe); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_I) { EB(0xce); }
	else if (reg1 == SPEC_REG_S && reg2 == SPEC_REG_S) { EB(0xf6); }
	else crash(state, "Unkown register combination in helper_combo_byte");
	return where;
}

void *helper_load_r8(vmstate_t *state, void *where, word_t reg)
{
	if      (reg == SPEC_REG_I) { EB3(0x4d, 0x89, 0xc8); }
	else if (reg == SPEC_REG_A) { EB3(0x4d, 0x89, 0xd0); }
	else if (reg == SPEC_REG_B) { EB3(0x4d, 0x89, 0xd8); }
	else if (reg == SPEC_REG_C) { EB3(0x4d, 0x89, 0xe0); }
	else if (reg == SPEC_REG_D) { EB3(0x4d, 0x89, 0xe8); }
	else if (reg == SPEC_REG_S) { EB3(0x4d, 0x89, 0xf0); }
	else if (reg == SPEC_REG_F) { EB3(0x4d, 0x89, 0xf8); }
	else crash(state, "Unknown register in helper_load_r8");
	return where;
}

void *helper_mov_imm(vmstate_t *state, void *where, word_t reg, unsigned long long value)
{
  if      (reg == SPEC_REG_A) { EB2(0x49, 0xba); } // r10
  else if (reg == SPEC_REG_B) { EB2(0x49, 0xbb); } // r11
  else if (reg == SPEC_REG_C) { EB2(0x49, 0xbc); } // r12
  else if (reg == SPEC_REG_D) { EB2(0x49, 0xbd); } // r13
  else if (reg == SPEC_REG_S) { EB2(0x49, 0xbe); } // r14
  else if (reg == SPEC_REG_F) { EB2(0x49, 0xbf); } // r15
  else if (reg == SPEC_REG_I) { EB2(0x49, 0xb9); } // r9
  else crash(state, "Unknown register in emit_imm");

  EQ(value);
  return where;
}

void *helper_jmp_i(vmstate_t *state, void *where)
{
	EB3(0x4d, 0x89, 0xc8); // mov r8, r9
	EB4(0x49, 0xc1, 0xe0, 0x03); // shl r8, 3
	EB2(0x48, 0xb8); EQ(state->instruction_offsets); // mov rax, state->instruction_offsets
	EB3(0x49, 0x01, 0xc0); // add r8, rax
	EB3(0x4d, 0x8b, 0x00); // mv r8, [r8]
	EB2(0x48, 0xb8); EQ(state->compiled_code); // mov rax, state->compiled_code
	EB3(0x49, 0x01, 0xc0); // add r8, rax
	EB3(0x41, 0xff, 0xe0); // jmp r8
	return where;
}

void *emit_imm(vmstate_t *state, void *where, instruction_t instruction)
{
  	TRACE("[e] compiling IMM %s = "WORD_FMT" to %p\n", describe_register(instruction.arg1), instruction.arg2, where);
  	where = helper_mov_imm(state, where, instruction.arg1, instruction.arg2);
  	if (instruction.arg1 == SPEC_REG_I) where = helper_jmp_i(state, where);
  	return where;
}

void *emit_add(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling ADD %s %s to %p\n", describe_register(instruction.arg1), describe_register(instruction.arg2), where);
	EB2(0x4d, 0x01); // add extended regs
	where = helper_combo_byte(state, where, instruction.arg1, instruction.arg2);
  	if (instruction.arg1 == SPEC_REG_I) where = helper_jmp_i(state, where);
	return where;
}

void *emit_stk(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling STK %s %s to %p\n", describe_register(instruction.arg1), describe_register(instruction.arg2), where);
	if (instruction.arg2)
	{
		EB4(0x49, 0x83, 0xc6, 0x8); // add r14, 8
		EB3(0x4d, 0x89, 0xf0); // mov r8, r14
		where = helper_store_mem(state, where, instruction.arg2);
	}
	if (instruction.arg1)
	{
		EB3(0x4d, 0x89, 0xf0); // mov r8, r14
		where = helper_load_mem(state, where, instruction.arg1);
		EB4(0x49, 0x83, 0xee, 0x8); // sub r14, 8
  		if (instruction.arg1 == SPEC_REG_I) where = helper_jmp_i(state, where);
	}
	return where;
}

void *emit_stm(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling STM *%s = %s to %p\n", describe_register(instruction.arg1), describe_register(instruction.arg2), where);
	where = helper_load_r8(state, where, instruction.arg1);
	where = helper_store_mem(state, where, instruction.arg2);
	return where;
}

void *emit_ldm(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling LDM %s = *%s to %p\n", describe_register(instruction.arg1), describe_register(instruction.arg2), where);
	where = helper_load_r8(state, where, instruction.arg2);
	where = helper_load_mem(state, where, instruction.arg1);
  	if (instruction.arg1 == SPEC_REG_I) where = helper_jmp_i(state, where);
	return where;
}

void *emit_cmp(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling CMP %s %s to %p\n", describe_register(instruction.arg1), describe_register(instruction.arg2), where);
	EB2(0x4d, 0x39); // add extended regs
	where = helper_combo_byte(state, where, instruction.arg1, instruction.arg2);
	return where;
}

void *emit_jmp(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling JMP %s %s to %p\n", describe_flags(instruction.arg1), describe_register(instruction.arg2), where);
	if (instruction.arg1) crash(state, "conditional jumps not supported in JIT mode");

	// update I
	EB2(0x4d, 0x89);
	where = helper_combo_byte(state, where, SPEC_REG_I, instruction.arg2);
	where = helper_jmp_i(state, where);
	return where;
}

void *emit_sys(vmstate_t *state, void *where, instruction_t instruction)
{
	TRACE("[e] compiling SYS "WORD_FMT" %s to %p\n", instruction.arg1, describe_register(instruction.arg2), where);
	crash(state, "ULTIMATE SANDBOX MODE: SYS instruction is not authorized for student use!");
	return where;
}

void *emit_end(vmstate_t *state, void *where)
{
	TRACE("[e] compiling terminating ret to %p\n", where);
	EB(0xc3);
	return where;
}

void *emit_instruction(vmstate_t *state, void *where, instruction_t instruction)
{
	if (instruction.op & INST_IMM) { where = emit_imm(state, where, instruction); }
	if (instruction.op & INST_ADD) { where = emit_add(state, where, instruction); }
	if (instruction.op & INST_STK) { where = emit_stk(state, where, instruction); }
	if (instruction.op & INST_STM) { where = emit_stm(state, where, instruction); }
	if (instruction.op & INST_LDM) { where = emit_ldm(state, where, instruction); }
	if (instruction.op & INST_CMP) { where = emit_cmp(state, where, instruction); }
	if (instruction.op & INST_JMP) { where = emit_jmp(state, where, instruction); }
	if (instruction.op & INST_SYS) { where = emit_sys(state, where, instruction); }
	return where;
}

void *emit_program(vmstate_t *state)
{
	void *where = state->compiled_code;

	// initialization
	TRACE("[e] emitting initialization code\n");
  	where = helper_mov_imm(state, where, SPEC_REG_A, 0);
  	where = helper_mov_imm(state, where, SPEC_REG_B, 0);
  	where = helper_mov_imm(state, where, SPEC_REG_C, 0);
  	where = helper_mov_imm(state, where, SPEC_REG_D, 0);
  	where = helper_mov_imm(state, where, SPEC_REG_S, 0);
  	where = helper_mov_imm(state, where, SPEC_REG_F, 0);
  	where = helper_mov_imm(state, where, SPEC_REG_I, 0);

	int i;
	for (i = 0; i < CODE_LENGTH; i++)
	{
		state->instruction_offsets[i] = (unsigned long long)where - (unsigned long long)state->compiled_code;
		TRACE("[e] instruction %d to %p (offset %#x from base)\n", i, where, state->instruction_offsets[i]);
		//EB3(0x49, 0xff, 0xc1);
		EB3(0x49, 0xc7, 0xc1); ED(i);
		where = emit_instruction(state, where, state->code[i]);
	}
	TRACE("[e] compiled %d instructions!\n", i);
	where = emit_end(state, where);
	return where;
}
