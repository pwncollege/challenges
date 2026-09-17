#include <assert.h>
#include <err.h>
#include <sys/mman.h>

#include <checkpoint.h>

int main(void)
{
    int *value = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    int *visits = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                      MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    assert(value != MAP_FAILED && visits != MAP_FAILED);
    *value = 42;

    long generation = checkpoint();
    assert(generation >= 0 && generation == (*visits)++);
    assert(*value == 42);
    if (generation == 3)
        return 0;

    *value = 99;
    assert(munmap(value, 4096) == 0);
    restore();
    errx(1, "restore returned to its caller");
}
