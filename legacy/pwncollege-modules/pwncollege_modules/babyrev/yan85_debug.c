char *describe_register(word_t reg_spec)
{
  if (reg_spec == SPEC_REG_A) return "a";
  if (reg_spec == SPEC_REG_B) return "b";
  if (reg_spec == SPEC_REG_C) return "c";
  if (reg_spec == SPEC_REG_D) return "d";
  if (reg_spec == SPEC_REG_S) return "s";
  if (reg_spec == SPEC_REG_I) return "i";
  if (reg_spec == SPEC_REG_F) return "f";
  if (reg_spec == 0) return "NONE";
  return "?";
}

char *describe_instruction(instruction_t instruction)
{
  if (instruction.op & INST_IMM) return "imm";
  if (instruction.op & INST_ADD) return "add";
  if (instruction.op & INST_STK) return "stk";
  if (instruction.op & INST_STM) return "stm";
  if (instruction.op & INST_LDM) return "ldm";
  if (instruction.op & INST_CMP) return "cmp";
  if (instruction.op & INST_JMP) return "jmp";
  if (instruction.op & INST_SYS) return "sys";
  return "???";
}

char flag_description[8] = { 0 };
char *describe_flags(word_t arg)
{
  int i = 0;
  if (arg & FLAG_L) { flag_description[i] = 'L'; i++; }
  if (arg & FLAG_G) { flag_description[i] = 'G'; i++; }
  if (arg & FLAG_E) { flag_description[i] = 'E'; i++; }
  if (arg & FLAG_N) { flag_description[i] = 'N'; i++; }
  if (arg & FLAG_Z) { flag_description[i] = 'Z'; i++; }
  if (arg == 0) { flag_description[i] = '*'; i++; }
  flag_description[i] = 0;
  return flag_description;
}
