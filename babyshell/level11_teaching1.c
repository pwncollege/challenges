#include <sys/mman.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>
#include <unistd.h>
#include <stdio.h>

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

unsigned long sp;
unsigned long bp;
unsigned long sz;
unsigned long cp;
unsigned long cv;
unsigned long si;
unsigned long rp;

#define GET_SP(sp) __asm__ __volatile(".intel_syntax noprefix; mov %0, rsp; .att_syntax;" : "=r"(sp) : : );
#define GET_BP(bp) __asm__ __volatile(".intel_syntax noprefix; mov %0, rbp; .att_syntax;" : "=r"(bp) : : );
#define GET_CANARY(cn) __asm__ __volatile(".intel_syntax noprefix; mov %0, QWORD PTR [fs:0x28]; .att_syntax;" : "=r"(cn) : : );
#define GET_FRAME_WORDS(sz, sp, bp, rp) GET_SP(sp); GET_BP(bp); sz = (bp-sp)/8+2; rp = bp+8;
#define FIND_CANARY(cnp, cv, start)                                     \
  {                                                                     \
    cnp = start;                                                        \
    GET_CANARY(cv);                                                     \
    while (*(unsigned long *)cnp != cv) cnp = (unsigned long)cnp - 8;   \
  }

void DUMP_STACK(unsigned long sp, unsigned long n)
{
    printf("+---------------------------------+-------------------------+--------------------+\n");
    printf("| %31s | %23s | %18s |\n", "Stack location", "Data (bytes)", "Data (LE int)");
    printf("+---------------------------------+-------------------------+--------------------+\n");
    for (si = 0; si < n; si++)
    {
        printf("| 0x%016lx (rsp+0x%04x) | %02x %02x %02x %02x %02x %02x %02x %02x | 0x%016lx |\n",
               sp+8*si, 8*si,
               *(unsigned char *)(sp+8*si+0), *(unsigned char *)(sp+8*si+1), *(unsigned char *)(sp+8*si+2), *(unsigned char *)(sp+8*si+3),
               *(unsigned char *)(sp+8*si+4), *(unsigned char *)(sp+8*si+5), *(unsigned char *)(sp+8*si+6), *(unsigned char *)(sp+8*si+7),
               *(unsigned long *)(sp+8*si)
              );
    }
    printf("+---------------------------------+-------------------------+--------------------+\n");
}

void *shellcode_mem;
size_t shellcode_size;

int main(int argc, char **argv, char **envp)
{
    assert(argc > 0);

    printf("###\n");
    printf("### Welcome to %s!\n", argv[0]);
    printf("###\n");
    printf("\n");
    printf("This challenge reads in some bytes, modifies them (depending on the specific\n");
    printf("challenge configuration, and executes them as code! This is a common exploitation\n");
    printf("scenario, called \"code injection\". Through this series of challenges, you will\n");
    printf("practice your shellcode writing skills under various constraints!\n");
    printf("\n");

    printf("To ensure that you are shellcoding, rather than doing other tricks, this\n");
    printf("will sanitize all environment variables and arguments and close all file\n");
    printf("descriptors > 2,\n");
    printf("\n");

    for (int i = 3; i < 10000; i++) close(i);
    for (char **a = argv; *a != NULL; a++) memset(*a, 0, strlen(*a));
    for (char **a = envp; *a != NULL; a++) memset(*a, 0, strlen(*a));

    shellcode_mem = mmap((void *) 0x2ff1e000, 0x4000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);

    printf("Mapping shellcode memory at %p.\n", shellcode_mem);

    assert(shellcode_mem == (void *) 0x2ff1e000);

    printf("\n");
    printf("Your shellcode will be read into memory at %p and executed. In this challenge,\n", shellcode_mem);
    printf("this address is constant across executions, so your shellcode can hard-code\n");
    printf("some addresses. Later challenges might not be so forgiving...\n");
    printf("\n");

    printf("Reading %#x bytes from stdin into %p.\n", 0x4000, shellcode_mem);

    shellcode_size = read(0, shellcode_mem, 0x4000);
    assert(shellcode_size > 0);

    printf("\n");
    printf("This challenge is about to execute the following shellcode:\n");
    printf("\n");
    print_disassembly(shellcode_mem, shellcode_size);
    printf("\n");

    printf("This challenge is about to close stdin, which means that it will be\n");
    printf("harder to pass in a stage-2 shellcode. You will need to figure an\n");
    printf("alternate solution (such as unpacking shellcode in memory) to get\n");
    printf("past complex filters...\n");
    printf("\n");
    assert(fclose(stdin) == 0);

    printf("This challenge is about to close stderr, which means that you will\n");
    printf("not be able to use file descriptor 2 for output. You might still\n");
    printf("be able to use file descriptor 1 (stdout), unless this challenge\n");
    printf("closes it as well.\n");
    printf("\n");
    assert(fclose(stderr) == 0);

    printf("Closing stdout. You will see no further output, and will need to figure\n");
    printf("out an alternate way of communicating data back to yourself.\n");
    printf("\n");
    assert(fclose(stdout) == 0);

    puts("Executing shellcode!\n");
    ((void(*)())shellcode_mem)();

}
