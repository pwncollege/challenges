#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <sys/stat.h>
#include "libkbfs/kbfs.h"

#define ROOT_DIR_BLOCK KBFS_META_BLOCK_NUM
#define FILE_TABLE_BLOCK (KBFS_META_BLOCK_NUM+1)
#define FILE_CONTENT_BLOCK (KBFS_META_BLOCK_NUM+2)

#define FILE_DNO KBFS_ROOTDNODE+1

#define FNAME "hello"
#define CONTENT "hello world!"

char content[0x18];
//#define CONTENT content

char block[KBFS_BLOCKSIZE];
u64 fsize;
struct kbfs_bitmap bitmap;

void write_super_block(int fd)
{
	struct kbfs_volume_header *vh = (struct kbfs_volume_header *)block;
	memset(block, 0, sizeof(block));
	vh->magic = KBFS_MAGIC;
	vh->version = KBFS_VERSION;
	vh->block_size = KBFS_BLOCKSIZE;
	vh->total_block = fsize / KBFS_BLOCKSIZE;
	assert(vh->total_block > KBFS_META_BLOCK_NUM+2); // besize the metadata, +2 for the root dentry and the file

	int ret = write(fd, block, KBFS_BLOCKSIZE);
	assert(ret == KBFS_BLOCKSIZE);
}

void write_dnode_store(int fd)
{
	int ret;
	struct kbfs_dnode *dnodes = (struct kbfs_dnode *)block;
	struct kbfs_dnode *root_dnode = &dnodes[KBFS_ROOTDNODE];
	struct kbfs_dnode *file_dnode = &dnodes[FILE_DNO];
	memset(block, 0, sizeof(block));

	// root diretory disk node
	root_dnode->mode = S_IFDIR | 0755;
	root_dnode->inuse = 1;
	root_dnode->uid = 0; // root
	root_dnode->gid = 0; // root
	root_dnode->size = KBFS_BLOCKSIZE;
	// root_dnode->blocks already cleared
	root_dnode->table = ROOT_DIR_BLOCK;

	// file1 disk node
	file_dnode->mode = S_IFREG | 0755;
	file_dnode->inuse = 1;
	//file_dnode->uid = 0; // root
	//file_dnode->gid = 0; // root
	file_dnode->uid = 1000; // user
	file_dnode->gid = 1000; // user
	file_dnode->size = sizeof(CONTENT);
	//file_dnode->size = 0x41414141;
	// file_dnode->blocks already cleared
	file_dnode->table = FILE_TABLE_BLOCK;

	ret = write(fd, block, KBFS_BLOCKSIZE);
	assert(ret == KBFS_BLOCKSIZE);
}

void write_bitmap(int fd)
{
	u64 total_block = fsize / KBFS_BLOCKSIZE;

	for(int i=0; i<KBFS_BLOCKSIZE; i++) {
		bitmap.map[i] = KBFS_BLOCK_FREE;
	}
	bitmap.map[KBFS_SUPER_BLOCK] = KBFS_BLOCK_INUSE;
	bitmap.map[KBFS_DNODE_BLOCK] = KBFS_BLOCK_INUSE;
	bitmap.map[KBFS_BITMAP_BLOCK] = KBFS_BLOCK_INUSE;
	bitmap.map[ROOT_DIR_BLOCK] = KBFS_BLOCK_INUSE;
	bitmap.map[FILE_TABLE_BLOCK] = KBFS_BLOCK_INUSE;
	bitmap.map[FILE_CONTENT_BLOCK] = KBFS_BLOCK_INUSE;

	assert(total_block >= FILE_CONTENT_BLOCK);
	for(int i=total_block; i<KBFS_BLOCKSIZE; i++) {
		bitmap.map[i] = KBFS_BLOCK_INVALID;
	}

	int ret = write(fd, bitmap.map, KBFS_BLOCKSIZE);
	assert(ret == KBFS_BLOCKSIZE);
}

void write_dentry_block(int fd)
{
	struct kbfs_dentry *dentry = (struct kbfs_dentry *)block;
	memset(block, 0, sizeof(block));

	dentry->entry_cnt = 1; // 1 file in it
	dentry->fentry[0].dnode_no = FILE_DNO;
	//dentry->fentry[1].dnode_no = FILE_DNO+1;
	strcpy(dentry->fentry[0].fname, FNAME);

	int ret = write(fd, block, KBFS_BLOCKSIZE);
	assert(ret == KBFS_BLOCKSIZE);
}

void write_file_table_block(int fd)
{
	memset(block, 0, sizeof(block));
	struct kbfs_block_table *table = (struct kbfs_block_table*)block;
	table->table[0] = FILE_CONTENT_BLOCK;

	int ret = write(fd, block, KBFS_BLOCKSIZE);
	assert(ret == KBFS_BLOCKSIZE);
}

void write_file_data_block(int fd)
{
	memset(block, 0, sizeof(block));
	memset(content, 'C', sizeof(content));
	content[sizeof(content)-1] = 0;
	strcpy(block, CONTENT);

	int ret = write(fd, block, KBFS_BLOCKSIZE);
	assert(ret == KBFS_BLOCKSIZE);
}

int main(int argc, char *argv[])
{
	if (argc < 2) {
		printf("usage: %s <device>", argv[0]);
		exit(-1);
	}

	int fd = open(argv[1], O_RDWR | O_NOFOLLOW);
	assert(fd >= 0);

	// get file size to calculate available blocks
	off_t ret = lseek(fd, 0, SEEK_END);
	assert(ret != (off_t)-1);
	fsize = (u64)ret;

	ret = lseek(fd, 0, SEEK_SET);
	assert(ret == 0);

	// format the disk image
	write_super_block(fd);
	write_dnode_store(fd);
	write_bitmap(fd);
	write_dentry_block(fd);
	write_file_table_block(fd);
	write_file_data_block(fd);
}
