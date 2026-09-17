#include <assert.h>
#include <err.h>
#include <fcntl.h>

#include <checkpoint.h>

int main(void)
{
    int fd = open("/tmp/duplicates", O_CREAT | O_TRUNC | O_RDWR, 0600);
    int alias = dup(fd);
    int independent = open("/tmp/duplicates", O_RDWR);
    assert(fd >= 0 && alias >= 0 && independent >= 0);
    assert(lseek(fd, 1, SEEK_SET) == 1);
    assert(lseek(independent, 3, SEEK_SET) == 3);

    long generation = checkpoint();
    assert(generation >= 0);
    if (generation == 0) {
        assert(dup2(independent, alias) == alias);
        assert(lseek(fd, 5, SEEK_SET) == 5);
        assert(lseek(alias, 7, SEEK_SET) == 7);
        restore();
        errx(1, "restore returned to its caller");
    }

    assert(generation == 1);
    assert(lseek(fd, 0, SEEK_CUR) == 1);
    assert(lseek(alias, 0, SEEK_CUR) == 1);
    assert(lseek(independent, 0, SEEK_CUR) == 3);
    assert(lseek(alias, 9, SEEK_SET) == 9);
    assert(lseek(fd, 0, SEEK_CUR) == 9);
    assert(lseek(independent, 0, SEEK_CUR) == 3);
    return 0;
}
