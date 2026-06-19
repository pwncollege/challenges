#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/proc_fs.h>
#include <linux/vmalloc.h>
#include <linux/device.h>
#include <linux/sched.h>
#include <linux/pid.h>
#include <linux/mm.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("pwn.college");
MODULE_DESCRIPTION("pwn.college challenge");
MODULE_VERSION("1.0");

static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static long device_ioctl(struct file *, unsigned int, unsigned long);

{% if challenge.device_mmap %}
  static int device_mmap(struct file *, struct vm_area_struct *);
{% endif %}

{% if challenge.load_flag %}
  {% if challenge.spectre_v1 %}
      static int prefix_len;
      static char *prefix = "FLAG: ";
  {% endif %}

  static char flag[128];

  {% if challenge.spectre_v2 %}
      static char safe_flag[128];
  {% endif %}
{% endif %}

struct proc_dir_entry *proc_entry = NULL;

static struct file_operations fops = {
  .open = device_open,
  .release = device_release,
  .unlocked_ioctl = device_ioctl,
  {% if challenge.device_mmap %}
    .mmap = device_mmap,
  {% endif %}
};

int init_module(void)
{
  pr_info("###\n");
  pr_info("### Welcome to this architecture challenge!\n");
  pr_info("###\n");

  pr_info("This challenge will misuse the kernel in a way that will teach you about micro-architectural vulnerabilities.\n");

  pr_info("This challenge exposes a simple character device interface through `/proc/pwncollege`.\n");
  pr_info("You can open and close this device as you would any other file.\n");

  pr_info("This device supports interactions through an ioctl interface.\n");

  {% if challenge.device_mmap %}
    pr_info("This device supports being mmaped via file descriptor.\n");
  {% endif %}

  {% if challenge.load_flag %}
    struct file *f;

    f = filp_open("/flag", O_RDONLY, 0);
    memset(flag, 0, 128);

    {% if challenge.spectre_v1 %}
        prefix_len = strlen(prefix);
        strncpy(flag, prefix, prefix_len);
        kernel_read(f, flag+prefix_len, 128-prefix_len, &f->f_pos);

    {% endif %}

    {% if challenge.spectre_v2 %}
        kernel_read(f, flag, 128, &f->f_pos);
        strcpy(safe_flag, "pwm.college");
    {% endif %}

    {% if challenge.meltdown_kern_flag %}
      pr_info("Meltdown mitigations are disabled for this challenge.\n", &flag);
      pr_info("The flag is in kernel memory at address %#lx\n", &flag);

      f = filp_open("/flag", O_RDONLY, 0);
      kernel_read(f, flag, 128, &f->f_pos);
    {% endif %}

    filp_close(f, NULL);

  {% endif %}

  {% if challenge.meltdown_user_flag %}
    pr_info("Meltdown mitigations are disabled for this challenge.\n");
    pr_info("The flag can be read by the userspace binary.\n");
    pr_info("This module has two ioctl commands\n\t1337 => touch a memory address\n\t31337 => get the address of a process's task_struct by pid.\n");
  {% endif %}

  proc_entry = proc_create("pwncollege", {{ challenge.device_permissions }}, NULL, &fops);

  pr_info("Good luck!\n");

  return 0;
}

void cleanup_module(void)
{
  if (proc_entry)
    proc_remove(proc_entry);
}

static int device_release(struct inode *inode, struct file *file)
{
  {% if walkthrough %}
    pr_info("[device_release] inode=%px, file=%px\n", inode, file);
  {% endif %}
  {% if challenge.device_mmap %}
    vfree(file->private_data);
  {% endif %}
  return 0;
}

{% if challenge.spectre_v1 %}
  static int device_open(struct inode *inode, struct file *file)
  {
    {% if walkthrough %}
      pr_info("[device_open] inode=%px, file=%px\n", inode, file);
    {% endif %}

    {% if challenge.device_mmap %}
      file->private_data = vmalloc_user(256*PAGE_SIZE);
    {% endif %}
    return 0;
  }

  __attribute__((target("sse2")))
  static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
  {
      char *shmem = file->private_data;
      uint32_t untrusted_idx;
      uint32_t limit = prefix_len;
      volatile char c = 0;

      untrusted_idx = shmem[0];
      if (unlikely((float)untrusted_idx / (float)limit < 1)) {
          c = shmem[flag[untrusted_idx] * PAGE_SIZE];
      }
    return 0;
  }
{% endif %}

{% if challenge.spectre_v2 %}
  static int device_open(struct inode *inode, struct file *file)
  {
    {% if walkthrough %}
      pr_info("[device_open] inode=%px, file=%px\n", inode, file);
    {% endif %}

    {% if challenge.device_mmap %}
      file->private_data = vmalloc_user(256*PAGE_SIZE);
    {% endif %}
    return 0;
  }

  // v2 roughly based on https://github.com/Anton-Cao/spectrev2-poc/blob/master/spectrev2.c
  int gadget(char *addr, char *shmem)
  {
      return shmem[(*addr)*PAGE_SIZE];
  }

  int safe(char *addr, char *shmem)
  {
      return 0;
  }

  int noinline victim(char *addr, char *shmem, int input, uint64_t* target)
  {
    volatile int result, junk;
    int i = 0;

    clflush((void *)target);
    __asm volatile( "mfence\n" );

    // need to do inline asm for call so it doesn't get retpoline'd
    __asm volatile (
      ".intel_syntax noprefix\n"
      "mov rdi, %2\n"
      "mov rsi, %3\n"
      "call qword ptr [%1]\n"
      "mov %0, eax\n"
      ".att_syntax\n"
      : "=r" (result)
      : "r" (target), "r" (addr), "r" (shmem)
      : "rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"
      );
    return result & junk;
  }

  static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
  {
      char *shmem = file->private_data;
      volatile char c = 0;
      volatile int result;
      unsigned int i, junk;

      unsigned int off = ((uint8_t*)shmem)[0];
      if (off > strlen(flag))
          return -1;

      uint64_t *target = (uint64_t *)gadget;

      unsigned int iters = ((uint8_t*)shmem)[1];
      for (i = 0; i < iters; i++) {
          junk ^= victim(safe_flag+off, shmem, 0, (uint64_t*)&target);
      }

      target = (uint64_t *)safe;
      __asm volatile( "mfence\n" );

      junk ^= victim(flag+off, shmem, 0, (uint64_t*)&target);

      return 0;
  }
{% endif %}



{% if challenge.meltdown_kern_flag %}
  static int device_open(struct inode *inode, struct file *file)
  {
      return 0;
  }

  // touches the flag to make meltdown possible (data needs to be present in cache)
  static long device_ioctl(struct file *filp, unsigned int ioctl_num, unsigned long ioctl_param) {
      int flag_len;
      volatile char c;
      int i;

      flag_len = strlen(flag);
      for ( i = 0; i < flag_len; i++ ) {
          c = flag[i];
      }
      return 0;
  }
{% endif %}

{% if challenge.meltdown_user_flag %}
  static int device_open(struct inode *inode, struct file *file)
  {
      return 0;
  }

  struct ioctl_struct {
      pid_t pid;                // provide this
      struct task_struct *task; // receive this
  };

  static long device_ioctl(struct file *filp, unsigned int ioctl_num, unsigned long ioctl_param)
  {
      struct ioctl_struct data;
      volatile char c;
      char *addr;
      pid_t pid;
      int ret;

      switch (ioctl_num) {
          case 31337:
              ret = copy_from_user(&data, (const void __user *)ioctl_param, sizeof(struct ioctl_struct));
              if (ret) return -EFAULT;

              data.task = pid_task(find_vpid(data.pid), PIDTYPE_PID);

              ret = copy_to_user((const void __user *)ioctl_param, &data, sizeof(struct ioctl_struct));
              if (ret) return -EFAULT;
              break;
          case 1337:
              addr = ioctl_param;
              c = *((char *)ioctl_param);
              break;
      }
      return 0;
  }
{% endif %}


{% if challenge.device_mmap %}
  static int device_mmap(struct file *file, struct vm_area_struct *vma)
  {
      if (remap_vmalloc_range(vma, file->private_data, 0) < 0)
          return -1;

      return 0;
  }
{% endif %}
