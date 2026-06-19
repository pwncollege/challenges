typedef unsigned char u8;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;
typedef int block_t;

struct kbfs_fentry;

// volume configuration
#define KBFS_BLOCKSIZE 0x1000
#define KBFS_MAGIC 0x5346424b // KBFS
#define KBFS_VERSION 1

// volume block format
#define KBFS_SUPER_BLOCK 0
#define KBFS_DNODE_BLOCK 1
#define KBFS_BITMAP_BLOCK 2
#define KBFS_DATA_BLOCK_START 3
#define KBFS_META_BLOCK_NUM KBFS_DATA_BLOCK_START
#define KBFS_ROOTDNODE 0
#define KBFS_FILE_MAX_SIZE KBFS_BLOCKSIZE/sizeof(u8)*KBFS_BLOCKSIZE

// volume directory/file format
#define KBFS_FILENAME_MAXLEN (0xf8-1)

/* a block-based filesystem
 * super block / volume header + padding	| 1 block
 * dnode store								| 1 block
 * bitmap block 							| 1 block
 * data blocks
 *
 * directory information is stored in one block
 * */

struct kbfs_volume_header // it will be stored in little endian in the disk image, which is not conventional
{
	u32 magic;
	u32 version;
	u32 block_size;
	u32 total_block;
};

struct kbfs_dnode // disk node, similar to VFS inode, don't use the name inode for differetiation
{
	u16 mode;
	u16 inuse;
	u16 uid;
	u16 gid;
	u64 size;
	u32 table; // if dnode is a directory, table points to dentry table, or it is a block index table
};

enum {
	KBFS_BLOCK_FREE,
	KBFS_BLOCK_INUSE,
	KBFS_BLOCK_INVALID
};

struct kbfs_bitmap
{
	u8 map[KBFS_BLOCKSIZE]; // 0: FREE, 1: INUSE, 2: INVALID
};

#define KBFS_DNODE_MAX (KBFS_BLOCKSIZE/sizeof(struct kbfs_dnode))
#define KBFS_VOLUME_MAX_SIZE KBFS_DNODE_MAX*KBFS_FILE_MAX_SIZE

struct kbfs_fentry
{
	u64 dnode_no;
	char fname[KBFS_FILENAME_MAXLEN];
};

#define KBFS_FENTRY_SIZE_MAX ((KBFS_BLOCKSIZE-sizeof(u64)) / sizeof(struct kbfs_fentry))

struct kbfs_dentry // directory entry, similar to VFS dentry, in KBFS
{
	u64 entry_cnt;
	struct kbfs_fentry fentry[KBFS_FENTRY_SIZE_MAX];
};

struct kbfs_block_table
{
	u8 table[KBFS_BLOCKSIZE]; // < KBFS_DATA_BLOCK_START: invalid
};
