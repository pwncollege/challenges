#define _GNU_SOURCE 1

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/signal.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/sendfile.h>
#include <sys/prctl.h>
#include <sys/personality.h>
#include <arpa/inet.h>

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

void *shellcode;
size_t shellcode_size;

int main(int argc, char **argv, char **envp)
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("###\n");
    printf("### Welcome to %s!\n", argv[0]);
    printf("###\n");
    printf("\n");

    puts("This challenge reads in some bytes, modifies them (depending on the specific challenge configuration), and executes them");
    puts("as code! This is a common exploitation scenario, called `code injection`. Through this series of challenges, you will");
    puts("practice your shellcode writing skills under various constraints! To ensure that you are shellcoding, rather than doing");
    puts("other tricks, this will sanitize all environment variables and arguments and close all file descriptors > 2.\n");
    for (int i = 3; i < 10000; i++) close(i);
    for (char **a = argv; *a != NULL; a++) memset(*a, 0, strlen(*a));
    for (char **a = envp; *a != NULL; a++) memset(*a, 0, strlen(*a));

    puts("In this challenge, shellcode will be copied onto the stack and executed. Since the stack location is randomized on every");
    puts("execution, your shellcode will need to be *position-independent*.\n");
    uint8_t shellcode_buffer[0x1000];
    shellcode = (void *)&shellcode_buffer;
    printf("Allocated 0x1000 bytes for shellcode on the stack at %p!\n", shellcode);

    puts("Reading 0x1000 bytes from stdin.\n");
    shellcode_size = read(0, shellcode, 0x1000);
    assert(shellcode_size > 0);

    puts("Executing filter...\n");
    puts("This challenge will randomly skip up to 0x800 bytes in your shellcode. You better adapt to that! One way to evade this");
    puts("is to have your shellcode start with a long set of single-byte instructions that do nothing, such as `nop`, before the");
    puts("actual functionality of your code begins. When control flow hits any of these instructions, they will all harmlessly");
    puts("execute and then your real shellcode will run. This concept is called a `nop sled`.\n");
    srand(time(NULL));
    int to_skip = (rand() % 0x700) + 0x100;
    shellcode += to_skip;
    shellcode_size -= to_skip;

    puts("This challenge is about to execute the following shellcode:\n");
    print_disassembly(shellcode, shellcode_size);
    puts("");

    puts("Executing shellcode!\n");
    ((void(*)())shellcode)();

    printf("### Goodbye!\n");
}