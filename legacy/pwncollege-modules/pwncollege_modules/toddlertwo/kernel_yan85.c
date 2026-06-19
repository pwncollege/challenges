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

#define MAX_FDS 8
#define SECCOMP_VIOLATION -42

{% if walkthrough %}
  #define TRACE printk
{% else %}
  #define TRACE(fmt, ...)
{% endif %}

{% set yan85_extra_vmstate_fields %}
  struct file *files[MAX_FDS];
  int signal;
  int (*sys_open)(struct vmstate *, char *, int, int);
  int (*sys_read)(struct vmstate *, int, void *, size_t);
  int (*sys_write)(struct vmstate *, int, void *, size_t);
  int (*sys_exit)(struct vmstate *, int);
  int (*sys_sleep)(struct vmstate *, int);
{% endset %}

{% include "babyrev/yan85_common.c" %}

{% include "toddlertwo/kernel_yan85_syscall.c" %}

{% if walkthrough %}
  {% include "babyrev/yan85_debug.c" %}
{% endif %}

{% include "babyrev/yan85_interpreter.c" %}

#undef sys_open
#undef sys_read
#undef sys_write
#undef sys_exit
#undef sys_sleep

{% if challenge.yan85_seccomp %}
  void yan85_seccomp_validate(vmstate_t *state)
  {
    instruction_t next_instruction = state->code[(state->regs.i) % CODE_LENGTH];

    if ((next_instruction.op & INST_SYS) &&
        (next_instruction.arg1 & (SYS_READ_CODE | SYS_READ_MEMORY))) {
      state->signal = SECCOMP_VIOLATION;
      pr_info("SECCOMP: violated\n");
    }
    else {
      pr_info("SECCOMP: validated\n");
    }
  }
{% endif %}

static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static int device_mmap(struct file *, struct vm_area_struct *);
static long device_ioctl(struct file *, unsigned int, unsigned long);

struct proc_dir_entry *proc_entry = NULL;
vmstate_t state = { 0 };

static struct file_operations fops = {
  .open = device_open,
  .release = device_release,
  .mmap = device_mmap,
  .unlocked_ioctl = device_ioctl,
};

int init_module(void)
{
  proc_entry = proc_create("ypu", {{ challenge.device_permissions }}, NULL, &fops);

  pr_info("###\n");
  pr_info("### Welcome to this kernel challenge!\n");
  pr_info("###\n");

  {% if walkthrough %}
    pr_info("This is a device driver for a YPU (yan85 processing unit).\n");
  {% endif %}

  return 0;
}

void cleanup_module(void)
{
  if (proc_entry) proc_remove(proc_entry);
}

static int device_open(struct inode *inode, struct file *file)
{
  {% if walkthrough %}
    pr_info("[device_open] inode=%px, file=%px\n", inode, file);
  {% endif %}

  file->private_data = vmalloc_user(0x1000);

  return 0;
}

static int device_release(struct inode *inode, struct file *file)
{
  {% if walkthrough %}
    pr_info("[device_release] inode=%px, file=%px\n", inode, file);
  {% endif %}

  vfree(file->private_data);

  return 0;
}

static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
  vmstate_t state = { 0 };
  instruction_t next_instruction;

  {% if walkthrough %}
    pr_info("[device_ioctl] file=%px, cmd=%du, arg=%lu\n", file, cmd, arg);
  {% endif %}

  if (cmd != 1337)
    return -1;

  state.code = file->private_data;
  state.sys_open = sys_open;
  state.sys_read = sys_read;
  state.sys_write = sys_write;
  state.sys_exit = sys_exit;
  state.sys_sleep = sys_sleep;

  while (state.regs.i != MAX_WORD_VALUE) {
    {% if challenge.yan85_seccomp %}
      yan85_seccomp_validate(&state);
    {% endif %}
    if (state.signal) {
      {% if challenge.yan85_seccomp %}
        if (state.signal == SECCOMP_VIOLATION)
          pr_info("Machine ABORTED due to: secure computation violation\n");
        else
      {% endif %}
        pr_info("Machine EXITED with signal: %d\n", state.signal);
      break;
    }
    next_instruction = state.code[(state.regs.i++) % CODE_LENGTH];
    interpret_instruction(&state, next_instruction);
  }

  return 0;
}

static int device_mmap(struct file *file, struct vm_area_struct *vma)
{
  {% if walkthrough %}
    pr_info("[device_mmap] file=%px, vma=%px\n", file, vma);
  {% endif %}

  if (remap_vmalloc_range(vma, file->private_data, 0) < 0)
      return -1;

  return 0;
}
