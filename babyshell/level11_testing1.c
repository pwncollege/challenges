#include <sys/mman.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>
#include <unistd.h>
#include <stdio.h>

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

    for (int i = 3; i < 10000; i++) close(i);
    for (char **a = argv; *a != NULL; a++) memset(*a, 0, strlen(*a));
    for (char **a = envp; *a != NULL; a++) memset(*a, 0, strlen(*a));

    shellcode_mem = mmap((void *) 0x18d30000, 0x4000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);

    printf("Mapping shellcode memory at %p.\n", shellcode_mem);

    assert(shellcode_mem == (void *) 0x18d30000);

    printf("Reading %#x bytes from stdin into %p.\n", 0x4000, shellcode_mem);

    shellcode_size = read(0, shellcode_mem, 0x4000);
    assert(shellcode_size > 0);

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
