#define _GNU_SOURCE 1
#include <sys/sendfile.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <time.h>

#include <seccomp.h>

#include <capstone/capstone.h>

#define CAPSTONE_ARCH CS_ARCH_X86
#define CAPSTONE_MODE CS_MODE_64

void print_disassembly(void *shellcode_addr, size_t shellcode_size)
{
    csh handle;
    cs_insn *insn;
    size_t count;

    if (cs_open(CAPSTONE_ARCH, CAPSTONE_MODE, &handle) != CS_ERR_OK)
    {
        printf("ERROR: disassembler failed to initialize.\n");
        return;
    }

    count = cs_disasm(handle, shellcode_addr, shellcode_size, (uint64_t)shellcode_addr, 0, &insn);
    if (count > 0)
    {
        size_t j;
        printf("      Address      |                      Bytes                    |          Instructions\n");
        printf("------------------------------------------------------------------------------------------\n");

        for (j = 0; j < count; j++)
        {
            printf("0x%016lx | ", (unsigned long)insn[j].address);
            for (int k = 0; k < insn[j].size; k++) printf("%02hhx ", insn[j].bytes[k]);
            for (int k = insn[j].size; k < 15; k++) printf("   ");
            printf(" | %s %s\n", insn[j].mnemonic, insn[j].op_str);
        }

        cs_free(insn, count);
    }
    else
    {
        printf("ERROR: Failed to disassemble shellcode! Bytes are:\n\n");
        printf("      Address      |                      Bytes\n");
        printf("--------------------------------------------------------------------\n");
        for (unsigned int i = 0; i <= shellcode_size; i += 16)
        {
            printf("0x%016lx | ", (unsigned long)shellcode_addr+i);
            for (int k = 0; k < 16; k++) printf("%02hhx ", ((uint8_t*)shellcode_addr)[i+k]);
            printf("\n");
        }
    }

    cs_close(&handle);
}
int main(int argc, char **argv)
{
    printf("[+] Welcome to %s!\n", argv[0]);

    puts("[+] This challenge will chroot into a jail in /tmp/jail-XXXXXX.");
    puts("[+] You will be able to easily read a fake flag file inside this jail,");
    puts("[+] not the real flag file outside of it.");
    puts("[+] If you want the real flag, you must escape.");

    puts("[+] You may open a specified file, as given by the first argument to the program (argv[1]).");

    puts("[+] You may also upload custom shellcode to do whatever you want.");

    puts("[+] For extra security, this challenge will only allow certain system calls!");

    puts("[!] Let's get started!");

    assert(argc > 1);

    puts("[.] Checking to make sure you're not trying to open the flag");
    assert(strstr(argv[1], "flag") == NULL);

    printf("[.] open()ing the specified path (%s)\n", argv[1]);
    int fd = open(argv[1], O_NOFOLLOW);

    puts("[.] Creating the jail");

    char jail_path[] = "/tmp/jail-XXXXXX";
    assert(mkdtemp(jail_path) != NULL);

    printf("[.] chroot()ing into the jail in %s\n", jail_path);
    assert(chroot(jail_path) == 0);

    puts("[.] chdir()ing into the new /");
    assert(chdir("/") == 0);

    puts("[.] Creating the fake /flag");
    int fffd = open("/flag", O_WRONLY | O_CREAT);
    write(fffd, "FLAG{FAKE}", 10);
    close(fffd);

    void *shellcode_addr = mmap((void *)0x1337000, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
    assert((unsigned char *)shellcode_addr == (unsigned char *)0x1337000);

    printf("[.] Mapped %#x bytes for shellcode at %p\n", 0x1000, (void *)0x1337000);

    printf("[.] Reading %#x bytes of shellcode from stdin\n", 0x1000);
    int actual_size = read(0, shellcode_addr, 0x1000);

    puts("[.] This is the shellcode that I read in and am about to execute:");
    print_disassembly(shellcode_addr, actual_size);

    puts("[.] Restricting system calls:");
    scmp_filter_ctx ctx;
    ctx = seccomp_init(SCMP_ACT_KILL);
    printf("Allowing syscall: %s (number %i)\n", "chdir", SCMP_SYS(chdir));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(chdir), 0) == 0);
    printf("Allowing syscall: %s (number %i)\n", "chroot", SCMP_SYS(chroot));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(chroot), 0) == 0);
    printf("Allowing syscall: %s (number %i)\n", "mkdir", SCMP_SYS(mkdir));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mkdir), 0) == 0);
    printf("Allowing syscall: %s (number %i)\n", "open", SCMP_SYS(open));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(open), 0) == 0);
    printf("Allowing syscall: %s (number %i)\n", "read", SCMP_SYS(read));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0) == 0);
    printf("Allowing syscall: %s (number %i)\n", "write", SCMP_SYS(write));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0) == 0);
    printf("Allowing syscall: %s (number %i)\n", "sendfile", SCMP_SYS(sendfile));
    assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(sendfile), 0) == 0);
    assert(seccomp_load(ctx) == 0);

    printf("Executing the shellcode. Good luck!\n");
    ((void(*)())shellcode_addr)();
}
