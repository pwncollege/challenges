#include <assert.h>
#include <err.h>
#include <errno.h>
#include <fcntl.h>

#include <checkpoint.h>

int main(void)
{
    int fd = open("/tmp/descriptor", O_CREAT | O_TRUNC | O_RDWR, 0600);
    assert(fd >= 0);
    assert(write(fd, "A", 1) == 1);
    assert(lseek(fd, 0, SEEK_SET) == 0);
    assert(fcntl(fd, F_SETFD, FD_CLOEXEC) == 0);
    int extra = fd + 1;
    assert(fcntl(extra, F_GETFD) == -1 && errno == EBADF);

    long generation = checkpoint();
    assert(generation >= 0);
    if (generation == 0) {
        assert(close(fd) == 0);
        assert(open("/dev/null", O_RDWR) == fd);
        assert(dup(fd) == extra);
        restore();
        errx(1, "restore returned to its caller");
    }

    assert(generation == 1);
    assert(fcntl(fd, F_GETFD) == FD_CLOEXEC);
    assert(fcntl(extra, F_GETFD) == -1 && errno == EBADF);
    char value;
    assert(read(fd, &value, 1) == 1 && value == 'A');
    return 0;
}
