#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/proc_fs.h>
#include <linux/mm.h>
#include <linux/vmalloc.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("pwn.college");
MODULE_DESCRIPTION("pwn.college challenge");
MODULE_VERSION("1.0");

#define TRACE(fmt, ...)
// #define TRACE printk

#define WORD_TYPE unsigned char

#define SPEC_REG_A 0x20
#define SPEC_REG_B 0x40
#define SPEC_REG_C 0x8
#define SPEC_REG_D 0x2
#define SPEC_REG_S 0x4
#define SPEC_REG_I 0x1
#define SPEC_REG_F 0x10

#define INST_IMM 0x20
#define INST_STK 0x40
#define INST_ADD 0x1
#define INST_STM 0x8
#define INST_LDM 0x80
#define INST_JMP 0x10
#define INST_CMP 0x2
#define INST_SYS 0x4

#define SYS_OPEN        0x8
#define SYS_READ_MEMORY 0x20
#define SYS_READ_CODE   0x1
#define SYS_WRITE       0x4
#define SYS_SLEEP       0x2
#define SYS_EXIT        0x10

#define FLAG_L 0x10
#define FLAG_G 0x4
#define FLAG_E 0x1
#define FLAG_N 0x8
#define FLAG_Z 0x2

#define INST_TYPE { unsigned char op; unsigned char arg1; unsigned char arg2; }
#define ADD_OPERATOR +
#define STACK_DIRECTION 1
#define WORD_FMT "%#hhx"

#define MAX_WORD_VALUE (((0x1ULL << ((sizeof(WORD_TYPE) * 8ULL) - 1ULL)) - 1ULL) | (0xFULL << ((sizeof(WORD_TYPE) * 8ULL) - 4ULL)))
#define CODE_LENGTH 256
#define MEM_LENGTH 256
#define MIN(x,y) x<y ? x : y

typedef struct INST_TYPE instruction_t;
typedef WORD_TYPE word_t;

char flag[256];

struct regstate_t
{
    word_t a;
    word_t b;
    word_t c;
    word_t d;
    word_t s;
    word_t i;
    word_t f;
};

typedef struct  vmstate
{
    word_t memory[MEM_LENGTH];
    instruction_t *code;

    struct regstate_t regs;

    int signal;
} vmstate_t;

int sys_exit(vmstate_t *state, int status);

void crash(vmstate_t *state, char *msg)
{
    TRACE("Machine CRASHED due to: %s\n", msg);
    sys_exit(state, 1);
}

int sys_exit(vmstate_t *state, int status)
{
    state->signal = status;
    return status;
}

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
    if (reg_spec == SPEC_REG_A)
    {
        state->regs.a = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_B)
    {
        state->regs.b = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_C)
    {
        state->regs.c = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_D)
    {
        state->regs.d = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_S)
    {
        state->regs.s = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_I)
    {
        state->regs.i = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_F)
    {
        state->regs.f = new_value;
        return;
    }
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

#define INSTRUCTION_ARGS instruction_t instruction
#define INSTRUCTION_ARG1 instruction.arg1
#define INSTRUCTION_ARG2 instruction.arg2

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

void interpret_instruction(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[V] a:"WORD_FMT" b:"WORD_FMT" c:"WORD_FMT" d:"WORD_FMT" s:"WORD_FMT" i:"WORD_FMT" f:"WORD_FMT"\n", state->regs.a, state->regs.b, state->regs.c, state->regs.d, state->regs.s, state->regs.i, state->regs.f);
    TRACE("[I] op:"WORD_FMT" arg1:"WORD_FMT" arg2:"WORD_FMT"\n", instruction.op, INSTRUCTION_ARG1, INSTRUCTION_ARG2);
    if (instruction.op & INST_IMM)
    {
        interpret_imm(state, instruction);
    }
    if (instruction.op & INST_ADD)
    {
        interpret_add(state, instruction);
    }
    if (instruction.op & INST_STK)
    {
        interpret_stk(state, instruction);
    }
    if (instruction.op & INST_STM)
    {
        interpret_stm(state, instruction);
    }
    if (instruction.op & INST_LDM)
    {
        interpret_ldm(state, instruction);
    }
    if (instruction.op & INST_CMP)
    {
        interpret_cmp(state, instruction);
    }
    if (instruction.op & INST_JMP)
    {
        interpret_jmp(state, instruction);
    }
}

static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static int device_mmap(struct file *, struct vm_area_struct *);
static long device_ioctl(struct file *, unsigned int, unsigned long);

struct proc_dir_entry *proc_entry = NULL;
vmstate_t state = { 0 };

static struct file_operations fops =
{
    .open = device_open,
    .release = device_release,
    .mmap = device_mmap,
    .unlocked_ioctl = device_ioctl,
};


int init_module(void)
{
    struct file *f;

    f = filp_open("/flag", O_RDONLY, 0);
    kernel_read(f, flag, MEM_LENGTH, &f->f_pos);

    proc_entry = proc_create("ypu", 0666, NULL, &fops);

    pr_info("###\n");
    pr_info("### Welcome to this architecture challenge!\n");
    pr_info("###\n");

    return 0;
}

void cleanup_module(void)
{
    if (proc_entry) proc_remove(proc_entry);
}

static int device_open(struct inode *inode, struct file *file)
{
    file->private_data = vmalloc_user(0x1000);
    return 0;
}

static int device_release(struct inode *inode, struct file *file)
{
    vfree(file->private_data);
    return 0;
}

static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    vmstate_t state = { 0 };
    instruction_t next_instruction;

    strcpy(state.memory, flag);

    if (cmd != 1337)
        return -1;

    state.code = file->private_data;

    while (state.regs.i != MAX_WORD_VALUE)
    {
        if (state.signal) { break; }
        next_instruction = state.code[(state.regs.i++) % CODE_LENGTH];
        interpret_instruction(&state, next_instruction);
        // TODO random sleep?
    }
    return 0;
}

static int device_mmap(struct file *file, struct vm_area_struct *vma)
{

    if (remap_vmalloc_range(vma, file->private_data, 0) < 0)
        return -1;

    return 0;
}

