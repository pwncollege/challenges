#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/proc_fs.h>
#include <linux/vmalloc.h>
#include <linux/cred.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("pwn.college");
MODULE_DESCRIPTION("pwn.college challenge");
MODULE_VERSION("1.0");

{% if challenge.shellcode_ioctl %}
  typedef struct {
    size_t length;
    unsigned char data[0x1000];
    void (*execute_addr)(void);
  } shellcode_t;
{% endif %}

static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);

{% if challenge.device_read %}
  static ssize_t device_read(struct file *, char *, size_t, loff_t *);
{% endif %}

{% if challenge.device_write %}
  static ssize_t device_write(struct file *, const char *, size_t, loff_t *);
{% endif %}

{% if challenge.device_ioctl %}
  static long device_ioctl(struct file *, unsigned int, unsigned long);
{% endif %}

{% if challenge.load_flag %}
  static char flag[128];
{% endif %}
{% if challenge.state_machine %}
  static char device_state = 0;
{% endif %}
{% if challenge.shellcode_write or challenge.shellcode_ioctl %}
  static unsigned char *shellcode;
{% endif %}
struct proc_dir_entry *proc_entry = NULL;

static struct file_operations fops = {
  .open = device_open,
  .release = device_release,

  {% if challenge.device_read %}
    .read = device_read,
  {% endif %}

  {% if challenge.device_write %}
    .write = device_write,
  {% endif %}

  {% if challenge.device_ioctl %}
    .unlocked_ioctl = device_ioctl,
  {% endif %}
};

{% if challenge.bin_padding %}
  static void __attribute__((used)) bin_padding(void)
  {
    asm volatile (".rept {{ challenge.bin_padding }}; nop; .endr");
  }
{% endif %}

{% if challenge.win_function %}
  static void __attribute__((used)) win(void)
  {
    pr_info("You win! Your current process has been elevated to root!\n");
    commit_creds(prepare_kernel_cred(0));
  }
{% endif %}

int init_module(void)
{
  {% if challenge.load_flag %}
    struct file *f;

    f = filp_open("/flag", O_RDONLY, 0);
    memset(flag, 0, 128);
    kernel_read(f, flag, 128, &f->f_pos);
    filp_close(f, NULL);
  {% endif %}

  {% if challenge.shellcode_write or challenge.shellcode_ioctl %}
    shellcode = __vmalloc(0x1000, GFP_KERNEL, PAGE_KERNEL_EXEC);
  {% endif %}

  proc_entry = proc_create("pwncollege", {{ challenge.device_permissions }}, NULL, &fops);

  pr_info("###\n");
  pr_info("### Welcome to this kernel challenge!\n");
  pr_info("###\n");

  {% if walkthrough %}
    pr_info("This challenge will misuse the kernel in a way that will teach you about basic kernel exploitation.\n");

    pr_info("This challenge exposes a simple character device interface through `/proc/pwncollege`.\n");
    pr_info("You can open, {% if challenge.device_read %}read, {% endif %}{% if challenge.device_write %}write, {% endif %}close this device as you would any other file.\n");
    {% if challenge.device_ioctl %}
      pr_info("This device also supports interactions through an ioctl interface.\n");
    {% endif %}

    {% if challenge.win_function %}
      pr_info("This kernel module defines a win function, which will elevate the calling process's privileges if called.\n");
    {% endif %}

    {% if challenge.state_machine %}
      pr_info("If you can figure out the password, the character device will allow you to read the flag.\n");
    {% endif %}

    {% if challenge.log_flag %}
      pr_info("If you can figure out the password, the character device will log the flag.\n");
    {% endif %}

    {% if challenge.call_function %}
      pr_info("The character device will allow you to call an arbitrary function inside the kernel.\n");
    {% endif %}

    {% if challenge.shellcode_write %}
      pr_info("The character device will execute any shellcode that you write to it inside the kernel.\n");
    {% endif %}

    {% if challenge.shellcode_ioctl %}
      pr_info("The character device will allow you to execute shellcode inside the kernel.\n");
    {% endif %}

    pr_info("Good luck!\n");
  {% endif %}

  return 0;
}

void cleanup_module(void)
{
  if (proc_entry)
    proc_remove(proc_entry);
}

static int device_open(struct inode *inode, struct file *file)
{
  {% if walkthrough %}
    pr_info("[device_open] inode=%px, file=%px\n", inode, file);
  {% endif %}
  return 0;
}

static int device_release(struct inode *inode, struct file *file)
{
  {% if walkthrough %}
    pr_info("[device_release] inode=%px, file=%px\n", inode, file);
  {% endif %}
  return 0;
}

{% if challenge.device_read %}
  static ssize_t device_read(struct file *file, char *buffer, size_t length, loff_t *offset)
  {
    char *response;

    {% if walkthrough %}
      pr_info("[device_read] file=%px, buffer=%px, length=%lu, offset=%px\n", file, buffer, length, offset);
    {% endif %}

    {% if challenge.state_machine %}
      switch (device_state) {
      case 0:
        response = "password:\n";
        break;
      case 1:
        response = "invalid password\n";
        device_state = 0;
        break;
      case 2:
        response = flag;
        break;
      default:
        response = "device error: unknown state\n";
        break;
      }

      return strlen(response) - copy_to_user(buffer, response, min(strlen(response), length));
    {% endif %}
  }
{% endif %}

{% set password_variables %}
  unsigned correct_password = false;
  char password[{{ challenge.input_size }}];
{% endset %}

{% macro password_check(buffer, length) %}
  copy_from_user(password, {{ buffer }}, min(sizeof(password), {{ length }}));
  if (!strncmp(password, "{{ challenge.input_solution }}", strlen("{{ challenge.input_solution }}"))) {
    correct_password = true;
  }
{% endmacro %}

{% if challenge.device_write %}
  static ssize_t device_write(struct file *file, const char *buffer, size_t length, loff_t *offset)
  {
    {% if challenge.password %}
      {{ password_variables }}
    {% endif %}

    {% if challenge.shellcode_write or challenge.kernel_log %}
      unsigned long remaining;
    {% endif %}

    {% if challenge.kernel_log %}
      struct {
          char buffer[256];
          int (*log_function)(const char *, ...);
      } logger = { 0 };
    {% endif %}

    ssize_t result = length;

    {% if walkthrough %}
      pr_info("[device_write] file=%px, buffer=%px, length=%lu, offset=%px\n", file, buffer, length, offset);
    {% endif %}

    {% if challenge.password %}
      {{ password_check("buffer", "length") }}
    {% endif %}

    {% if challenge.state_machine %}
      if (correct_password) {
        device_state = 2;
      }
      else {
        device_state = 1;
      }
    {% endif %}

    {% if challenge.log_flag %}
      if (correct_password) {
        pr_info("The flag is: %s\n", flag);
      }
    {% endif %}

    {% if challenge.win_function and challenge.password %}
      if (correct_password) {
        win();
      }
    {% endif %}

    {% if challenge.shellcode_write %}
      remaining = copy_from_user(shellcode, buffer, min((size_t) 4096, length));
      ((void(*)(void)) shellcode)();
      result = length - remaining;
    {% endif %}

    {% if challenge.kernel_log %}
      logger.log_function = printk;
      remaining = copy_from_user(&logger.buffer, buffer, length);
      logger.log_function(logger.buffer);
      result = length - remaining;
    {% endif %}

    return result;
  }
{% endif %}

{% if challenge.device_ioctl %}
  static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
  {
    {% if challenge.password %}
      {{ password_variables }}
    {% endif %}

    {% if challenge.shellcode_ioctl %}
      size_t shellcode_length;
      void (*shellcode_execute_addr)(void);
    {% endif %}

    {% if walkthrough %}
      pr_info("[device_ioctl] file=%px, cmd=%du, arg=%lu\n", file, cmd, arg);
    {% endif %}

    if (cmd != 1337)
      return -1;

    {% if challenge.password %}
      {{ password_check("(char *) arg", "sizeof(password)") }}
    {% endif %}

    {% if challenge.win_function and challenge.password %}
      if (correct_password) {
        win();
      }
    {% endif %}

    {% if challenge.call_function %}
      ((void(*)(void)) arg)();
    {% endif %}

    {% if challenge.shellcode_ioctl %}
      (void)! copy_from_user(&shellcode_length, &((shellcode_t *) arg)->length, sizeof(shellcode_length));
      (void)! copy_from_user(&shellcode_execute_addr, &((shellcode_t *) arg)->execute_addr, sizeof(shellcode_execute_addr));
      if (shellcode_length > 0x1000)
        return -2;
      (void)! copy_from_user(shellcode, &((shellcode_t *) arg)->data, shellcode_length);
      shellcode_execute_addr();
    {% endif %}

    return 0;
  }
{% endif %}
