#include <assert.h>
#include <err.h>
#include <fcntl.h>
#include <string.h>

#include <checkpoint.h>

int main(void)
{
    int fd = open("/tmp/file", O_CREAT | O_TRUNC | O_RDWR, 0600);
    assert(fd >= 0);
    assert(write(fd, "abcdef", 6) == 6);
    assert(lseek(fd, 2, SEEK_SET) == 2);

    long generation = checkpoint();
    assert(generation >= 0 && generation <= 2);
    assert(lseek(fd, 0, SEEK_CUR) == 2);
    if (generation > 0) {
        char contents[4];
        assert(pread(fd, contents, 4, 2) == 4);
        assert(memcmp(contents, "XYef", 4) == 0);
    }
    if (generation == 2)
        return 0;

    assert(write(fd, "XY", 2) == 2);
    assert(close(fd) == 0);
    restore();
    errx(1, "restore returned to its caller");
}
