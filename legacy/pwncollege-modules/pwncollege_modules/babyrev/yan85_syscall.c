int sys_open(vmstate_t *state, char *pathname, int flags, int mode)
{
    return open(pathname, flags);
}

int sys_read(vmstate_t *state, int fd, void *buf, size_t count)
{
    return read(fd, buf, count);
}

int sys_write(vmstate_t *state, int fd, void *buf, size_t count)
{
    return write(fd, buf, count);
}

int sys_exit(vmstate_t *state, int status)
{
    exit(status);
    return 0;
}

int sys_sleep(vmstate_t *state, int seconds)
{
    return sleep(seconds);
}
