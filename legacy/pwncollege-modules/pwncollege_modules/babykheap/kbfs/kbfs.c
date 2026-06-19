/*
 * A vulnerable kbfs driver implementation for education purpose :P
 * author: Kyle Zeng, @ky1ebot, <zengyhkyle@gmail.com>
 * reference:
 * - https://elixir.bootlin.com/linux/v6.7/source/fs/efs
 * - https://github.com/psankar/simplefs
 *
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/buffer_head.h>
#include <linux/delay.h>
#include "libkbfs/kbfs.h"

typedef unsigned long kbfs_ino_t;
#define KBFS_INFO(sb) ((struct kbfs_info*)sb->s_fs_info)
#undef printk
#undef pr_err
#undef pr_info
#undef pr_debug
#define printk(...)
#define pr_err(...)
#define pr_info(...)
#define pr_debug(...)

struct kbfs_inode {
	struct inode vfs_inode;
	u32 capacity;
	u32 table;
	{% if challenge.kbfs_df %}
	char *link;
	{% endif %}
};

struct kbfs_info {
	u16 uid;
	u16 gid;
	u8 bitmap[KBFS_BLOCKSIZE];
};

struct kbfs_vma_struct
{
	u64 vaddr;
	size_t size;
	struct list_head list;
};

static inline struct kbfs_inode *KBFS_INODE(struct inode *inode)
{
	return container_of(inode, struct kbfs_inode, vfs_inode);
}

static struct inode *kbfs_iget(struct super_block *super, kbfs_ino_t ino);

static struct kmem_cache * kbfs_inode_cachep;

/************************ Operations **************************/
static block_t kbfs_block(struct kbfs_inode *ki, off_t off)
{
	printk("kbfs_block: %llx, offset: %llx", (unsigned long long)ki, (unsigned long long)off);
	// translate inode offset to block number
	struct buffer_head *bh;
	struct kbfs_block_table *table;
	block_t block;
	u8 *bitmap;

	printk("i_size: 0x%llx", ki->vfs_inode.i_size);
	if (off >= KBFS_FILE_MAX_SIZE) return -EINVAL;
	if (off > ki->capacity || off < 0) return -EINVAL;

	if ((ki->vfs_inode.i_mode & S_IFMT) == S_IFDIR) return ki->table;

	bh = sb_bread(ki->vfs_inode.i_sb, ki->table);
	if (!bh) {
		pr_err("fail to read block\n");
		return -EIO;
	}
	table = (struct kbfs_block_table *)bh->b_data;
	block = table->table[off/KBFS_BLOCKSIZE];
	brelse(bh);

	bitmap = KBFS_INFO(ki->vfs_inode.i_sb)->bitmap;
	if(block >= 0 && block < KBFS_BLOCKSIZE && bitmap[block] == KBFS_BLOCK_INUSE) {
		return block;
	}
	return -EIO;
}

static int kbfs_no_link(struct dentry *old_dentry, struct inode *dir, struct dentry *new_dentry)
{
	pr_info("kbfs_no_link\n");
	return -EOPNOTSUPP;
}

static int kbfs_iterate_shared(struct file *filp, struct dir_context *ctx)
{

	struct inode *inode = file_inode(filp);
	struct kbfs_inode *ki = KBFS_INODE(inode);
	struct kbfs_dentry *kdentry;
	struct buffer_head *bh;
	u64 fentry_cnt;
	block_t block;

	pr_info("kbfs_iterate_shared with ctx->pos: %lld\n", ctx->pos);
	if (ctx->pos > 0) {
		ctx->pos = inode->i_size;
		return 0; // we do everything in one go
	}
	block = kbfs_block(ki, 0);
	pr_info("block: %d\n", block);
	if (block < 0) return block;

	bh = sb_bread(inode->i_sb, block);
	if (!bh) {
		pr_err("fail to read block\n");
		return -EIO;
	}
	kdentry = (struct kbfs_dentry *)bh->b_data;
	fentry_cnt = min(kdentry->entry_cnt, KBFS_FENTRY_SIZE_MAX);
	for (int i=0; i<fentry_cnt; i++) {
		struct kbfs_fentry *fentry;
		fentry = &kdentry->fentry[i];
		pr_info("fname: %s\n", fentry->fname);
		if (!dir_emit(ctx, fentry->fname, strlen(fentry->fname), fentry->dnode_no, DT_UNKNOWN)) {
			brelse(bh);
			return -EINVAL;
		}
	}
	brelse(bh);
	ctx->pos = inode->i_size;
	return 0;
}

static kbfs_ino_t kbfs_find_entry(struct inode *inode, const char *name, int len)
{
	struct kbfs_inode *ki = KBFS_INODE(inode);
	struct kbfs_dentry *kdentry;
	struct buffer_head *bh;
	u64 fentry_cnt;
	block_t block;

	pr_info("kbfs_find_entry, name: %s\n", name);
	if (len <= 0) return -EINVAL;
	block = kbfs_block(ki, 0);
	pr_info("block: %d\n", block);
	if (block < 0) return block;

	bh = sb_bread(inode->i_sb, block);
	if (!bh) {
		pr_err("fail to read block\n");
		return -EIO;
	}
	kdentry = (struct kbfs_dentry *)bh->b_data;
	fentry_cnt = min(kdentry->entry_cnt, KBFS_FENTRY_SIZE_MAX);
	for (int i=0; i<fentry_cnt; i++) {
		struct kbfs_fentry *fentry;
		fentry = &kdentry->fentry[i];
		if (!strncmp(fentry->fname, name, len)) return fentry->dnode_no;
	}
	brelse(bh);
	return -EINVAL;
}

static ssize_t kbfs_file_read_iter(struct kiocb *iocb, struct iov_iter *to)
{
	struct file *filp = iocb->ki_filp;
	struct inode *inode = file_inode(filp);
	struct kbfs_inode *ki = KBFS_INODE(inode);
	struct buffer_head *bh;
	size_t read_cnt = 0;
	size_t block_off;
	size_t to_read;
	block_t block;

	if (!is_sync_kiocb(iocb)) return -EINVAL;
	if (iocb->ki_pos < 0 || iocb->ki_pos > inode->i_size) return -EINVAL;

	pr_info("kbfs_file_read_iter: pos: 0x%llx, cnt: 0x%lx\n", iocb->ki_pos, iov_iter_count(to));
	while (iocb->ki_pos < inode->i_size && iov_iter_count(to)) {
		size_t left = inode->i_size - iocb->ki_pos;
		// first, read out the relevant block
		block = kbfs_block(ki, iocb->ki_pos);
		printk("kbfs_block: %llx, %llx => %x\n", (unsigned long long)ki, iocb->ki_pos, block);
		if (block < 0) {
			printk("failed to find the block for offset: %llx", iocb->ki_pos);
			return block;
		}
		block_off = iocb->ki_pos % KBFS_BLOCKSIZE;
		to_read = min(KBFS_BLOCKSIZE - block_off, left);
		to_read = min(to_read, iov_iter_count(to));

		bh = sb_bread(inode->i_sb, block);
		if (!bh) {
			pr_err("fail to read block\n");
			return -EIO;
		}
		pr_info("%llx %llx\n", (unsigned long long)bh, (unsigned long long)inode->i_sb);
		pr_info("read_from_buffer: 0x%lx, 0x%lx\n", (unsigned long)bh->b_data, to_read);
		if(_copy_to_iter(bh->b_data+block_off, to_read, to) != to_read) {
			pr_info("copy_to_iter fails\n");
			brelse(bh);
			return -EIO;
		}
		brelse(bh);
		iocb->ki_pos += to_read;
		read_cnt += to_read;
	}

	pr_info("kbfs_file_read_iter read_cnt: 0x%lx\n", read_cnt);
	return read_cnt;
}

static ssize_t kbfs_file_write_iter(struct kiocb *iocb, struct iov_iter *from)
{
	struct file *filp = iocb->ki_filp;
	struct inode *inode = file_inode(filp);
	struct kbfs_inode *ki = KBFS_INODE(inode);
	struct buffer_head *bh;
	size_t write_cnt = 0;
	size_t block_off;
	size_t to_write;
	block_t block;

	if (!is_sync_kiocb(iocb)) return -EINVAL;
	if (iocb->ki_pos < 0 || iocb->ki_pos + iov_iter_count(from) > ki->capacity) return -EINVAL;
	if (iocb->ki_pos > inode->i_size) return -EINVAL; // do not support sparse file

	pr_info("kbfs_file_write_iter: %lx, %llx\n", iov_iter_count(from), iocb->ki_pos);
	while(iov_iter_count(from) > 0) {
		size_t left = ki->capacity - iocb->ki_pos;

		block = kbfs_block(ki, iocb->ki_pos);
		printk("kbfs_block: %llx, %llx => %x\n", (unsigned long long)ki, iocb->ki_pos, block);
		if (block < 0) {
			printk("failed to find the block for offset: %llx", iocb->ki_pos);
			return block;
		}
		block_off = iocb->ki_pos % KBFS_BLOCKSIZE;
		to_write = min(KBFS_BLOCKSIZE - block_off, left);
		to_write = min(to_write, iov_iter_count(from));

		bh = sb_bread(inode->i_sb, block);
		if (!bh) {
			pr_err("fail to load block\n");
			return -EIO;
		}
		pr_info("%llx %llx\n", (unsigned long long)bh, (unsigned long long)inode->i_sb);
		pr_info("write_to_buffer: 0x%lx\n", (unsigned long)bh->b_data);
		if(_copy_from_iter(bh->b_data+block_off, to_write, from) != to_write) {
			brelse(bh);
			return -EIO;
		}
		brelse(bh);
		iocb->ki_pos += to_write;
		write_cnt += to_write;
		if (iocb->ki_pos > inode->i_size) inode->i_size = iocb->ki_pos;
	}
	return write_cnt;
}

struct kbfs_vma_struct *kbfs_vma_alloc(void)
{
	struct kbfs_vma_struct *kb_vma = kzalloc(sizeof(struct kbfs_vma_struct), GFP_KERNEL);
	if (IS_ERR(kb_vma)) return NULL;
	INIT_LIST_HEAD(&kb_vma->list);
	return kb_vma;
}

int kbfs_file_open(struct inode *inode, struct file *filp)
{
	struct kbfs_vma_struct *kb_vma;
	pr_info("[kbfs] kbfs_file_open\n");
	if (filp->f_flags & O_APPEND) generic_file_llseek(filp, 0, SEEK_END);
	kb_vma = kbfs_vma_alloc();
	if(!kb_vma) return -ENOMEM;
	kb_vma->vaddr = 0;
	kb_vma->size = 0;
	filp->private_data = kb_vma;
	return 0;
}

void kbfs_vma_cleanup(struct file *filp)
{
	struct kbfs_vma_struct *kb_vma_root = filp->private_data;
	struct kbfs_vma_struct *kb_vma;
	struct list_head *pos = NULL;
	struct list_head *tmp;

	list_for_each_prev_safe(pos, tmp, &kb_vma_root->list) {
		kb_vma = list_entry(pos, struct kbfs_vma_struct, list);
		list_del(pos);
		if(kb_vma->vaddr == 0) continue;
		free_pages(kb_vma->vaddr, get_order(kb_vma->size));
		//printk("clean up kb_vma: 0x%lx\n", (unsigned long)(kb_vma->vaddr));
		kfree(kb_vma);
	}
	kfree(kb_vma_root);
	filp->private_data = NULL;
}

int kbfs_file_release(struct inode *inode, struct file *filp)
{
	pr_info("[kbfs] kbfs_file_release\n");
	kbfs_vma_cleanup(filp);
	return 0;
}

int kbfs_file_setattr(struct mnt_idmap *idmap, struct dentry *dentry, struct iattr *iattr)
{
	struct inode *inode = d_inode(dentry);
	struct kbfs_inode *ki = KBFS_INODE(inode);
	int error;

	error = setattr_prepare(idmap, dentry, iattr);
	if (error)
		return error;

	if (iattr->ia_valid & ATTR_SIZE) {
		if (iattr->ia_size > ki->capacity)
			return -EINVAL;
		inode->i_size = iattr->ia_size;
	}
	if (iattr->ia_valid & ATTR_MODE)
		return -EINVAL;
	setattr_copy(idmap, inode, iattr);
	mark_inode_dirty(inode);
	return 0;
}

int kbfs_file_mmap(struct file *filp, struct vm_area_struct *vma)
{
	size_t size;
	size_t max_size;
	struct inode *inode = file_inode(filp);
	struct kbfs_vma_struct *kb_vma;
	struct kbfs_inode *ki = KBFS_INODE(inode);
	unsigned long pfn;
	int ret = 0;

	printk("[kbfs] mmap, vm_start: 0x%lx, vm_end: 0x%lx, vm_pgoff: 0x%lx, vm_flags: 0x%lx!\n", vma->vm_start, vma->vm_end, vma->vm_pgoff, vma->vm_flags);
	if (vma->vm_flags & VM_SHARED) return -EINVAL; // we only do private mapping
	if (inode->i_sb->s_blocksize != PAGE_SIZE) return -EINVAL;

	size = vma->vm_end - vma->vm_start;
	max_size = (inode->i_size/PAGE_SIZE + (inode->i_size % PAGE_SIZE != 0)) * PAGE_SIZE; // round up by page_size
	{% if not challenge.kbfs_faulty_mmap %}
	if (vma->vm_pgoff * PAGE_SIZE + size > max_size) return -EINVAL; // bound check
	if (vma->vm_pgoff * PAGE_SIZE + size < size) return -EINVAL; // overflow check
	{% endif %}
	kb_vma = kbfs_vma_alloc();
	if (!kb_vma) return -ENOMEM;
	kb_vma->vaddr = __get_free_pages(GFP_KERNEL|__GFP_ZERO, get_order(max_size));
	if (!kb_vma->vaddr) {
		kfree(kb_vma);
		return -ENOMEM;
	}
	kb_vma->size = size;

	for(size_t off=0; off<max_size; off += PAGE_SIZE) {
		struct buffer_head *bh;
		size_t to_copy;
		block_t block = kbfs_block(ki, vma->vm_pgoff * PAGE_SIZE + off);
		if (block < 0) {
			pr_err("fail to read block\n");
			ret = -EIO;
			goto out;
		}
		bh = sb_bread(inode->i_sb, block);
		if (!bh) {
			pr_err("fail to read block\n");
			ret = -EIO;
			goto out;
		}
		to_copy = min(PAGE_SIZE, inode->i_size - off);
		//pr_info("mmap, to_copy: 0x%lx\n", to_copy);
		memcpy((void *)(kb_vma->vaddr+off), (void *)bh->b_data, to_copy);
		brelse(bh);
	}
	pfn = __pa((void*)(kb_vma->vaddr)) >> PAGE_SHIFT;
	if (remap_pfn_range(vma, vma->vm_start, pfn, size, vma->vm_page_prot)) {
		pr_info("fail to remap\n");
		ret = -EAGAIN;
		goto out;
	}

	list_add(&kb_vma->list, &((struct kbfs_vma_struct *)filp->private_data)->list);
	printk("[kbfs] vaddr: 0x%llx, size: 0x%lx\n", kb_vma->vaddr, kb_vma->size);
	return 0;

out:
	free_pages(kb_vma->vaddr, get_order(max_size));
	kfree(kb_vma);
	return ret;
}

static struct dentry *kbfs_lookup(struct inode *dir, struct dentry *dentry, unsigned int flags)
{
	kbfs_ino_t ino;
	struct inode *inode = NULL;

	pr_info("kbfs_lookup\n");
	ino = kbfs_find_entry(dir, dentry->d_name.name, dentry->d_name.len);
	if (ino >= KBFS_DNODE_MAX) return NULL;
	if (ino) inode = kbfs_iget(dir->i_sb, ino);
	if (IS_ERR(inode)) return NULL;

	return d_splice_alias(inode, dentry);
}

void kbfs_put_link(void *arg)
{
	pr_info("kbfs_put_link! %lx\n", (unsigned long)arg);
	kfree(arg);
}

{% if challenge.kbfs_df %}
const char *kbfs_get_link(struct dentry *dentry, struct inode *inode,
			struct delayed_call *callback)
{
	pr_info("kbfs_get_link!");
	struct kbfs_inode *ki = KBFS_INODE(inode);

	if (!ki->link) return ERR_PTR(-EIO);

	set_delayed_call(callback, kbfs_put_link, ki->link);

	return (const char *)ki->link;
}
{% else %}
const char *kbfs_get_link(struct dentry *dentry, struct inode *inode,
			  struct delayed_call *callback)
{
	void *link;
	struct buffer_head *bh;
	pr_info("kbfs_get_link!");
	struct kbfs_inode *ki = KBFS_INODE(inode);
	block_t block = kbfs_block(ki, 0);

	if (block < 0) return ERR_PTR(-EIO);
	bh = sb_bread(inode->i_sb, block);
	if (!bh) {
		pr_err("fail to read block\n");
		return ERR_PTR(-EIO);
	}
	link = kmalloc(strlen(bh->b_data)+1, GFP_KERNEL_ACCOUNT);
	pr_info("link: 0x%lx", (unsigned long)link);
	if (!link) {
		brelse(bh);
		return ERR_PTR(-ENOMEM);
	}
	strcpy(link, bh->b_data);
	brelse(bh);

	set_delayed_call(callback, kbfs_put_link, link);

	return (const char *)link;
}
{% endif %}

const struct file_operations kbfs_dir_operations = {
	.iterate_shared	= kbfs_iterate_shared,
};

const struct file_operations kbfs_file_operations = {
	.open			= kbfs_file_open,
	.release		= kbfs_file_release,
	.read_iter		= kbfs_file_read_iter,
	.write_iter		= kbfs_file_write_iter,
	.mmap			= kbfs_file_mmap,
};

const struct inode_operations kbfs_dir_inode_operations = {
	.lookup			= kbfs_lookup,
};

const struct inode_operations kbfs_file_inode_operations = {
	.link			= kbfs_no_link,
	.setattr		= kbfs_file_setattr,
};

const struct inode_operations kbfs_symlink_inode_operations = {
	.get_link		= kbfs_get_link,
	.link			= kbfs_no_link
};

/*******************************************************************/

/************************ VFS Stuff **************************/
static struct inode *kbfs_alloc_inode(struct super_block *sb)
{
	struct kbfs_inode *ki;
	pr_info("kbfs_alloc_inode\n");
	ki = alloc_inode_sb(sb, kbfs_inode_cachep, GFP_KERNEL);
	if (!ki)
		return NULL;
	pr_info("alloced inode: %llx\n", (unsigned long long)(&ki->vfs_inode));
	return &ki->vfs_inode;
}

static void kbfs_free_inode(struct inode *inode)
{
	pr_info("kbfs_free_inode: %llx\n", (unsigned long long)inode);
	kmem_cache_free(kbfs_inode_cachep, KBFS_INODE(inode));
}

static void init_once(void *obj)
{
	struct kbfs_inode *ki = (struct kbfs_inode *) obj;
	// pr_info("init_once ki: %llx\n", (unsigned long long)(&ki->vfs_inode));

	inode_init_once(&ki->vfs_inode);
}

static int __init init_inodecache(void)
{
	kbfs_inode_cachep = kmem_cache_create("kbfs_inode_cache",
				sizeof(struct kbfs_inode), 0,
				SLAB_RECLAIM_ACCOUNT|SLAB_MEM_SPREAD|
				SLAB_ACCOUNT, init_once);
	if (kbfs_inode_cachep == NULL)
		return -ENOMEM;
	return 0;
}

static void destroy_inodecache(void)
{
	rcu_barrier();
	kmem_cache_destroy(kbfs_inode_cachep);
}

static const struct super_operations kbfs_superblock_operations;
static struct inode *kbfs_iget(struct super_block *super, kbfs_ino_t ino)
{
	struct inode *inode;
	struct kbfs_inode *ki;
	struct buffer_head *bh;
	struct kbfs_dnode *kbfs_dnode;
	struct kbfs_info *info;

	inode = iget_locked(super, ino);
	if (!(inode->i_state & I_NEW))
		return inode;
	ki = KBFS_INODE(inode);
	info = KBFS_INFO(ki->vfs_inode.i_sb);

	// translate kbfs disk node to VFS inode
	bh = sb_bread(inode->i_sb, KBFS_DNODE_BLOCK);
	if (!bh) {
		pr_err("fail to read block\n");
		return ERR_PTR(-EIO);
	}
	kbfs_dnode = ((struct kbfs_dnode *)bh->b_data) + ino;
	inode->i_mode = kbfs_dnode->mode;

	{% if challenge.kbfs_allow_root %}
	i_uid_write(inode, kbfs_dnode->uid);
	i_gid_write(inode, kbfs_dnode->gid);
	{% else %}
	i_uid_write(inode, info->uid);
	i_gid_write(inode, info->gid);
	{% endif %}

	inode->i_size = kbfs_dnode->size;
	ki->table = kbfs_dnode->table;
	inode_set_atime(inode, 0, 0);
	inode_set_mtime(inode, 0, 0);
	inode_set_ctime(inode, 0, 0);
	brelse(bh);

	// calculate the inode's capacity
	if (ki->table < KBFS_DATA_BLOCK_START) ki->capacity = 0;
	else {
		bh = sb_bread(inode->i_sb, ki->table);
		if (!bh) {
			pr_err("fail to read block\n");
			return ERR_PTR(-EIO);
		}
		struct kbfs_block_table *btable = (struct kbfs_block_table*)bh->b_data;
		ki->capacity = 0;
		for(int i=0; i<KBFS_BLOCKSIZE; i++) {
			if(btable->table[i] < KBFS_DATA_BLOCK_START) break;
			ki->capacity += KBFS_BLOCKSIZE;
		}
		brelse(bh);
	}

	// set number of blocks
	if (inode->i_size == 0) inode->i_blocks = 0;
	else inode->i_blocks = ((inode->i_size - 1) / KBFS_BLOCKSIZE) + 1;
	pr_info("kbfs_iget: inode: %ld, mode %o\n", ino, inode->i_mode);

	switch (inode->i_mode & S_IFMT) {
		case S_IFDIR:
			pr_info("S_IFDIR\n");
			if (inode->i_size != KBFS_BLOCKSIZE) {
				pr_err("malformed diretory size\n");
				goto failed;
			}
			inode->i_op = &kbfs_dir_inode_operations;
			inode->i_fop = &kbfs_dir_operations;
			break;
		case S_IFREG:
			pr_info("S_IFREG\n");
			inode->i_op = &kbfs_file_inode_operations;
			inode->i_fop = &kbfs_file_operations;
			break;
		{% if challenge.kbfs_df %}
		case S_IFLNK:
			block_t block;
			pr_info("S_IFLNK\n");
			inode->i_op = &kbfs_symlink_inode_operations;
			if (inode->i_size <= 0 || inode->i_size > KBFS_BLOCKSIZE) goto link_failed;
			block = kbfs_block(ki, 0);
			if (block < 0) goto link_failed;
			bh = sb_bread(inode->i_sb, block);
			if (!bh) {
				pr_err("fail to read block\n");
				goto link_failed;
			}
			ki->link = kmalloc(strlen(bh->b_data)+1, GFP_KERNEL_ACCOUNT);
			pr_info("ki->link: 0x%lx", (unsigned long)ki->link);
			if (!ki->link) {
				goto link_failed;
			}
			strcpy(ki->link, bh->b_data);
			brelse(bh);
			break;
		{% else %}
		case S_IFLNK:
			pr_info("S_IFLNK\n");
			inode->i_op = &kbfs_symlink_inode_operations;
			if (inode->i_size <= 0 || inode->i_size > KBFS_BLOCKSIZE) goto link_failed;
			break;
		{% endif %}
		default:
			pr_err("kbfs: unsupported inode mode %o\n", inode->i_mode);
			goto failed;
	}

	unlock_new_inode(inode);
	return inode;

failed:
	pr_warn("failed to read inode %lu\n", inode->i_ino);
	iget_failed(inode);
	return ERR_PTR(-EIO);
link_failed:
	pr_warn("failed to read iflnk inode %lu\n", inode->i_ino);
	kbfs_free_inode(inode);
	return ERR_PTR(-EIO);

}

static int kbfs_fill_super(struct super_block *s, void *d, int silent)
{
	struct buffer_head *bh;
	struct inode *root;
	struct kbfs_info *info;
	struct kbfs_volume_header *vh;

	// load the super block information
	// and validate volume header
	bh = sb_bread(s, KBFS_SUPER_BLOCK);
	if (!bh) {
		pr_err("fail to read volume header\n");
		return -EINVAL;
	}
	vh = (struct kbfs_volume_header*)bh->b_data;
	if (vh->magic != KBFS_MAGIC) goto vh_error;
	if (vh->version != KBFS_VERSION) goto vh_error;
	if (vh->block_size != KBFS_BLOCKSIZE) goto vh_error;
	if (vh->total_block < KBFS_DATA_BLOCK_START) goto vh_error;

	s->s_magic = KBFS_MAGIC;
	s->s_maxbytes = KBFS_VOLUME_MAX_SIZE;
	sb_set_blocksize(s, KBFS_BLOCKSIZE);

	brelse(bh);

	// load the block bitmap
	bh = sb_bread(s, KBFS_BITMAP_BLOCK);
	if (!bh) {
		pr_err("fail to read volume header\n");
		return -EINVAL;
	}
	info = kzalloc(sizeof(struct kbfs_info), GFP_KERNEL);
	s->s_fs_info = info;
	memcpy(info->bitmap, bh->b_data, KBFS_BLOCKSIZE);
	info->uid = from_kuid_munged(current_user_ns(), current_uid());
	info->gid = from_kgid_munged(current_user_ns(), current_gid());
	brelse(bh);

	// load the root inode
	s->s_op = &kbfs_superblock_operations;
	root = kbfs_iget(s, KBFS_ROOTDNODE);
	if (!root) return -EINVAL;
	s->s_root = d_make_root(root);

	return 0;

vh_error:
	brelse(bh);
	return -EINVAL;
}

static struct dentry *kbfs_mount(struct file_system_type *fs_type,
	int flags, const char *dev_name, void *data)
{
	pr_info("kbfs_mount\n");
	return mount_bdev(fs_type, flags, dev_name, data, kbfs_fill_super);
}

static void kbfs_kill_sb(struct super_block *s)
{
	pr_info("kbfs_kill_sb\n");
	kill_block_super(s);
}

struct file_system_type kbfs_fs_type = {
	.owner = THIS_MODULE,
	.name = "kbfs",
	.mount = kbfs_mount,
	.kill_sb = kbfs_kill_sb,
	{% if challenge.kbfs_user_ns %}
	.fs_flags	= FS_USERNS_MOUNT | FS_REQUIRES_DEV,
	{% else %}
	.fs_flags	= FS_REQUIRES_DEV,
	{% endif %}
};

static const struct super_operations kbfs_superblock_operations = {
	.alloc_inode	= kbfs_alloc_inode,
	.free_inode	= kbfs_free_inode,
};
MODULE_ALIAS_FS("kbfs");

/*******************************************************************/

/************************** Module Stuff ***************************/


static int kbfs_init(void)
{
	int ret;
	pr_info("kbfs_init\n");

	//mutex_init(&kbfs_mutex);;

	init_inodecache();

	ret = register_filesystem(&kbfs_fs_type);
	if(!ret) pr_info("registered kbfs filesystem successfully\n");
	else pr_err("fail to register kbfs filesystem!\n");

	return ret;
}

static void kbfs_exit(void)
{
	pr_info("kbfs_exit\n");

	pr_info("unregister kbfs filesystem!");
	unregister_filesystem(&kbfs_fs_type);

	destroy_inodecache();
}

module_init(kbfs_init);
module_exit(kbfs_exit);

MODULE_AUTHOR("Kyle Zeng <zengyhkyle@gmail.com>");
MODULE_DESCRIPTION("A vulnerable kbfs driver implementation for education purpose :P");
MODULE_LICENSE("Dual MIT/GPL");
/*******************************************************************/
