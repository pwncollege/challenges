#include <linux/fs.h>
#include <linux/io.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/string.h>
#include <linux/uaccess.h>

#define FLAG_ADDRESS 0x08000000
#define FLAG_SIZE 4096

static char *flag;
static size_t flag_length;
static bool unlocked;

static ssize_t flag_read(struct file *file, char __user *buffer,
                         size_t count, loff_t *offset)
{
    if (!READ_ONCE(unlocked))
        return -EACCES;

    return simple_read_from_buffer(buffer, count, offset, flag, flag_length);
}

static ssize_t flag_write(struct file *file, const char __user *buffer,
                          size_t count, loff_t *offset)
{
    char command[16];

    if (!count || count >= sizeof(command))
        return -EINVAL;
    if (copy_from_user(command, buffer, count))
        return -EFAULT;
    command[count] = '\0';

    if (!sysfs_streq(command, "please"))
        return -EINVAL;

    WRITE_ONCE(unlocked, true);
    return count;
}

static const struct file_operations flag_operations = {
    .owner = THIS_MODULE,
    .read = flag_read,
    .write = flag_write,
};

static struct miscdevice flag_device = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "flag",
    .fops = &flag_operations,
    .mode = 0666,
};

static int __init flag_init(void)
{
    int result;

    flag = memremap(FLAG_ADDRESS, FLAG_SIZE, MEMREMAP_WB);
    if (!flag)
        return -ENOMEM;

    flag_length = strnlen(flag, FLAG_SIZE);
    if (!flag_length || flag_length == FLAG_SIZE) {
        memunmap(flag);
        return -EINVAL;
    }

    result = misc_register(&flag_device);
    if (result)
        memunmap(flag);
    return result;
}

static void __exit flag_exit(void)
{
    misc_deregister(&flag_device);
    memunmap(flag);
}

module_init(flag_init);
module_exit(flag_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("A device with something to read, if you ask nicely.");
