word_t read_register(vmstate_t *state, word_t reg_spec)
{
  if (reg_spec == SPEC_REG_A) return state->regs.a;
  if (reg_spec == SPEC_REG_B) return state->regs.b;
  if (reg_spec == SPEC_REG_C) return state->regs.c;
  if (reg_spec == SPEC_REG_D) return state->regs.d;
  if (reg_spec == SPEC_REG_S) return state->regs.s;
  if (reg_spec == SPEC_REG_I) return state->regs.i;
  if (reg_spec == SPEC_REG_F) return state->regs.f;
  crash(state, "unknown register");
}

void write_register(vmstate_t *state, word_t reg_spec, word_t new_value)
{
  if (reg_spec == SPEC_REG_A) { state->regs.a = new_value; return; }
  if (reg_spec == SPEC_REG_B) { state->regs.b = new_value; return; }
  if (reg_spec == SPEC_REG_C) { state->regs.c = new_value; return; }
  if (reg_spec == SPEC_REG_D) { state->regs.d = new_value; return; }
  if (reg_spec == SPEC_REG_S) { state->regs.s = new_value; return; }
  if (reg_spec == SPEC_REG_I) { state->regs.i = new_value; return; }
  if (reg_spec == SPEC_REG_F) { state->regs.f = new_value; return; }
  crash(state, "unknown register");
}

word_t read_memory(vmstate_t *state, word_t address)
{
  return state->memory[address];
}

void write_memory(vmstate_t *state, word_t address, word_t value)
{
  state->memory[address] = value;
}

{% if challenge.direct_interpret_calls %}
#define INSTRUCTION_ARGS {{ challenge.word_type }} arg1, {{ challenge.word_type }} arg2
#define INSTRUCTION_ARG1 arg1
#define INSTRUCTION_ARG2 arg2
{% else %}
#define INSTRUCTION_ARGS instruction_t instruction
#define INSTRUCTION_ARG1 instruction.arg1
#define INSTRUCTION_ARG2 instruction.arg2
{% endif %}

void interpret_imm(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] IMM %s = "WORD_FMT"\n", describe_register(INSTRUCTION_ARG1), INSTRUCTION_ARG2);
  write_register(state, INSTRUCTION_ARG1, INSTRUCTION_ARG2);
}

void interpret_add(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] ADD %s %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
  write_register(state, INSTRUCTION_ARG1, read_register(state, INSTRUCTION_ARG1) ADD_OPERATOR read_register(state, INSTRUCTION_ARG2));
}

void interpret_stk(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] STK %s %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
  if (INSTRUCTION_ARG2)
  {
    TRACE("[s] ... pushing %s\n", describe_register(INSTRUCTION_ARG2));
    // push register in arg2
    state->regs.s += STACK_DIRECTION;
    write_memory(state, state->regs.s, read_register(state, INSTRUCTION_ARG2));
  }
  if (INSTRUCTION_ARG1)
  {
    // pop to arg1
    TRACE("[s] ... popping %s\n", describe_register(INSTRUCTION_ARG1));
    write_register(state, INSTRUCTION_ARG1, read_memory(state, state->regs.s));
    state->regs.s -= STACK_DIRECTION;
  }
}

void interpret_stm(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] STM *%s = %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
  write_memory(state, read_register(state, INSTRUCTION_ARG1), read_register(state, INSTRUCTION_ARG2));
}

void interpret_ldm(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] LDM %s = *%s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
  write_register(state, INSTRUCTION_ARG1, read_memory(state, read_register(state, INSTRUCTION_ARG2)));
}

void interpret_cmp(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] CMP %s %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
  word_t r1 = read_register(state, INSTRUCTION_ARG1);
  word_t r2 = read_register(state, INSTRUCTION_ARG2);
  state->regs.f = 0;
  if (r1 < r2) state->regs.f |= FLAG_L;
  if (r1 > r2) state->regs.f |= FLAG_G;
  if (r1 == r2) state->regs.f |= FLAG_E;
  if (r1 != r2) state->regs.f |= FLAG_N;
  if (r1 == 0 && r2 == 0) state->regs.f |= FLAG_Z;
}

void interpret_jmp(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[j] JMP %s %s\n", describe_flags(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
  if (!INSTRUCTION_ARG1 || (INSTRUCTION_ARG1 & state->regs.f))
  {
    TRACE("[j] ... TAKEN\n");
    state->regs.i = read_register(state, INSTRUCTION_ARG2);
  }
  else
  {
    TRACE("[j] ... NOT TAKEN\n");
  }
}

void interpret_sys(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[s] SYS "WORD_FMT" %s\n", INSTRUCTION_ARG1, describe_register(INSTRUCTION_ARG2));
  if (INSTRUCTION_ARG1 & SYS_OPEN)
  {
    {% if challenge.crash_correct %}
    puts("Success. Crashing!");
    int *crasher = NULL;
    *crasher = 0;
    sys_exit(1);
    {% endif %}
    {% if challenge.no_open %}
    crash(state, "Disallowed system call: SYS_OPEN");
    {% endif %}
    TRACE("[s] ... open\n");
    write_register(state, INSTRUCTION_ARG2, sys_open(state, (char*)(state->memory + state->regs.a), state->regs.b, state->regs.c));
  }
  {% if not challenge.direct_interpret_calls %}
  if (INSTRUCTION_ARG1 & SYS_READ_CODE)
  {
    {% if challenge.no_read_code %}
    crash(state, "Disallowed system call: SYS_READ_CODE");
    {% endif %}
    TRACE("[s] ... read_code\n");
    write_register(state, INSTRUCTION_ARG2, sys_read(state, state->regs.a, (char *)(state->code + state->regs.b), MIN(state->regs.c, sizeof(instruction_t)*(CODE_LENGTH-state->regs.b))));
  }
  {% endif %}
  if (INSTRUCTION_ARG1 & SYS_READ_MEMORY)
  {
    TRACE("[s] ... read_memory\n");
    char *read_buffer = (char *)(state->memory + state->regs.b);
    {% if challenge.read_overflow %}
    word_t read_length = state->regs.c;
    {% else %}
    word_t read_length = MIN(state->regs.c, sizeof(word_t)*(MEM_LENGTH-state->regs.b));
    {% endif %}
    write_register(state, INSTRUCTION_ARG2, sys_read(state, state->regs.a, read_buffer, read_length));
  }
  if (INSTRUCTION_ARG1 & SYS_WRITE)
  {
    TRACE("[s] ... write\n");
    char *write_buffer = (char *)(state->memory + state->regs.b);
    {% if challenge.write_overflow %}
    word_t write_length = state->regs.c;
    {% else %}
    word_t write_length = MIN(state->regs.c, sizeof(word_t)*(MEM_LENGTH-state->regs.b));
    {% endif %}
    write_register(state, INSTRUCTION_ARG2, sys_write(state, state->regs.a, write_buffer, write_length));
  }
  if (INSTRUCTION_ARG1 & SYS_SLEEP)
  {
    TRACE("[s] ... sleep\n");
    write_register(state, INSTRUCTION_ARG2, sys_sleep(state, state->regs.a));
  }
  if (INSTRUCTION_ARG1 & SYS_EXIT)
  {
    TRACE("[s] ... exit\n");
    sys_exit(state, state->regs.a);
  }
  if (INSTRUCTION_ARG2)
  {
    TRACE("[s] ... return value (in register %s): "WORD_FMT"\n", describe_register(INSTRUCTION_ARG2), read_register(state, INSTRUCTION_ARG2));
  }
  else
  {
  }
}

{% if challenge.direct_interpret_calls %}
void execute_program(vmstate_t *state)
{
  {% include "babyrev/yan85_hardcoded.c" %}
}
{% else %}

void interpret_instruction(vmstate_t *state, INSTRUCTION_ARGS)
{
  TRACE("[V] a:"WORD_FMT" b:"WORD_FMT" c:"WORD_FMT" d:"WORD_FMT" s:"WORD_FMT" i:"WORD_FMT" f:"WORD_FMT"\n", state->regs.a, state->regs.b, state->regs.c, state->regs.d, state->regs.s, state->regs.i, state->regs.f);
  TRACE("[I] op:"WORD_FMT" arg1:"WORD_FMT" arg2:"WORD_FMT"\n", instruction.op, INSTRUCTION_ARG1, INSTRUCTION_ARG2);
  if (instruction.op & INST_IMM) { interpret_imm(state, instruction); }
  if (instruction.op & INST_ADD) { interpret_add(state, instruction); }
  if (instruction.op & INST_STK) { interpret_stk(state, instruction); }
  if (instruction.op & INST_STM) { interpret_stm(state, instruction); }
  if (instruction.op & INST_LDM) { interpret_ldm(state, instruction); }
  if (instruction.op & INST_CMP) { interpret_cmp(state, instruction); }
  if (instruction.op & INST_JMP) { interpret_jmp(state, instruction); }
  if (instruction.op & INST_SYS) { interpret_sys(state, instruction); }
}

void interpreter_loop(vmstate_t *state)
{
  {% if challenge.interpret_forever %}
  while (1)
  {% else %}
  while (state->regs.i != MAX_WORD_VALUE)
  {% endif %}
  {
    instruction_t next_instruction = state->code[(state->regs.i++) % CODE_LENGTH];
    interpret_instruction(state, next_instruction);
  }
}

{% endif %}
