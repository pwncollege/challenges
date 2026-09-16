#include <unistd.h>

#define SYS_hello 470

int main(int argc, char **argv)
{
    for (int i = 1; i < argc; i++)
        syscall(SYS_hello, argv[i]);

    return 0;
}
