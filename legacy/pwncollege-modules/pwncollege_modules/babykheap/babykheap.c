#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/proc_fs.h>
#include <linux/vmalloc.h>
#include <linux/cred.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Kyle Zeng (@ky1ebot)");
MODULE_DESCRIPTION("pwn.college linux kernel heap-based exploitation challenge");
MODULE_VERSION("1.0");

static struct proc_dir_entry *proc_entry = NULL;
{% if challenge.isolated_cache %}
static struct kmem_cache *cachep = NULL;
{% endif %}
{% if challenge.flag_obj %}
char flag[0x100];
{% endif %}

typedef struct {
	{% if challenge.func_ptr %}
	void (*func)(char *);
	{% endif %}
	unsigned char data[0x1d0];
} kheap_obj_t;

typedef struct {
	void __user * ubuf;
	size_t size;
} kheap_req_t;

// define commands
#define IOCTL_BASE 'W'
#define CMD_READ       _IO(IOCTL_BASE, 0)
#define CMD_WRITE      _IO(IOCTL_BASE, 1)
#define CMD_CALL       _IO(IOCTL_BASE, 2)
#define CMD_RELEASE    _IO(IOCTL_BASE, 3)
#define CMD_FLAG       _IO(IOCTL_BASE, 4)

static int kheap_open(struct inode *, struct file *);
static long kheap_ioctl(struct file *, unsigned int, unsigned long);
static int kheap_release(struct inode *, struct file *);

static struct proc_ops kheap_fops = {
	.proc_open = kheap_open,
	.proc_ioctl = kheap_ioctl,
	.proc_release = kheap_release,
};

{% if challenge.func_ptr %}
static void do_print(char *str)
{
	pr_info("[kheap] %s\n", str);
}
{% endif %}

static kheap_obj_t *alloc_obj(void)
{
	kheap_obj_t *obj = NULL;
	{% if challenge.isolated_cache %}
	obj = kmem_cache_alloc(cachep, GFP_KERNEL_ACCOUNT);
	{% else %}
	obj = kmalloc(sizeof(kheap_obj_t), GFP_KERNEL_ACCOUNT);
	{% endif %}
	if (!obj) return NULL;
	memset(obj, 0, sizeof(kheap_obj_t));
	{% if challenge.func_ptr %}
	obj->func = do_print;
	{% endif %}
	return obj;
}

static void free_obj(void *obj)
{
	{% if challenge.isolated_cache %}
	kmem_cache_free(cachep, obj);
	{% else %}
	kfree(obj);
	{% endif %}
}

static int kheap_open(struct inode *inode, struct file *filp)
{
	pr_info("[kheap] device opened\n");
	filp->private_data = alloc_obj();
	if(!filp->private_data) return -ENOMEM;
	return 0;
}

static long kheap_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
	pr_info("[kheap] device ioctl\n");
	kheap_obj_t *obj = (kheap_obj_t*)filp->private_data;
	kheap_req_t req;

	if(copy_from_user(&req, (void*)arg, sizeof(req)))
		return -EINVAL;

	{% if not challenge.oob %}
	if(cmd != CMD_CALL && req.size > sizeof(obj->data))
		return -EINVAL;
	{% endif %}

	switch(cmd) {
		{% if not challenge.uaf_w %}
		case CMD_READ:
			if(copy_to_user(req.ubuf, obj->data, req.size))
				return -EFAULT;
			return 0;
		{% endif %}
		case CMD_WRITE:
			if(copy_from_user(obj->data, req.ubuf, req.size))
				return -EFAULT;
			return 0;
		{% if challenge.func_ptr %}
		case CMD_CALL:
			obj->func(obj->data);
			return 0;
		{% endif %}
		{% if challenge.uaf_rw or challenge.uaf_w %}
		case CMD_RELEASE:
			free_obj(obj);
			return 0;
		{% endif %}
		{% if challenge.flag_obj %}
		case CMD_FLAG:
			kheap_obj_t *obj = alloc_obj();
			strcpy(obj->data, flag);
			return 0;
		{% endif %}
		default:
			return -EINVAL;
	}
}

static int kheap_release(struct inode *inode, struct file *filp)
{
	pr_info("[kheap] device released\n");
	free_obj(filp->private_data);
	filp->private_data = NULL;
	return 0;
}

/*======================================= Module Stuff ========================================*/
static int __init kheap_init(void)
{
	{% if challenge.flag_obj %}
	struct file *f;
	int ret;

	f = filp_open("/flag", O_RDONLY, 0);
	if (!f) return -ENOENT;
	memset(flag, 0, sizeof(flag));
	ret = kernel_read(f, flag, sizeof(flag), &f->f_pos);
	if (ret < 0) return -EIO;
	filp_close(f, NULL);
	{% endif %}

	{% if challenge.isolated_cache %}
	cachep = kmem_cache_create("kheap_obj", sizeof(kheap_obj_t), 0,
			SLAB_HWCACHE_ALIGN|SLAB_PANIC|SLAB_ACCOUNT|SLAB_NO_MERGE, NULL);
	if (!cachep) return -ENOMEM;
	{% endif %}

	proc_entry = proc_create("kheap", 0666, NULL, &kheap_fops);
	if (!proc_entry) return -EINVAL;
	return 0;
}

static void __exit kheap_exit(void)
{
	if (proc_entry)
		proc_remove(proc_entry);

	{% if challenge.isolated_cache %}
	kmem_cache_destroy(cachep);
	{% endif %}
}

module_init(kheap_init);
module_exit(kheap_exit);
