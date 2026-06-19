int sys_open(vmstate_t *state, char *pathname, int flags, int mode)
{
  int fd;
  struct file *file;

  for (fd = 0; fd < MAX_FDS; fd++) {
    if (state->files[fd] == NULL) {
      file = filp_open(pathname, flags, mode);
      if (IS_ERR(file))
          fd = -1;
      else
          state->files[fd] = file;
      return fd;
    }
  }

  return -1;
}

int sys_read(vmstate_t *state, int fd, void *buf, size_t count)
{
  {% if challenge.yan85_seccomp_harden %}
    char buffer[256];
    int result;
    int i;
    char c;
  {% endif %}

  struct file *file = state->files[fd];
  if (!file)
    return -1;

  {% if challenge.yan85_seccomp_harden %}
    result = kernel_read(file, buffer, min(count, sizeof(buffer)), &file->f_pos);
    for (i = 0; i < result; i++) {
      c = buffer[i];
      if (c == '{' || c == '}') {
        state->signal = SECCOMP_VIOLATION;
        pr_info("SECCOMP: violated\n");
        return -1;
      }
    }
    memcpy(buf, buffer, result);
    return result;

  {% else %}
    return kernel_read(file, buf, count, &file->f_pos);
  {% endif %}
}

int sys_write(vmstate_t *state, int fd, void *buf, size_t count)
{
  struct file *file = state->files[fd];
  if (!file)
    return -1;
  return kernel_write(file, buf, count, &file->f_pos);
}

int sys_exit(vmstate_t *state, int status)
{
  state->signal = status;
  return status;
}

int sys_sleep(vmstate_t *state, int seconds)
{
  int i;
  int j;
  for (i = 0; i < seconds; i++)
    for (j = 0; j < 1000000; j++);
  return seconds;
}

#define sys_open state->sys_open
#define sys_read state->sys_read
#define sys_write state->sys_write
#define sys_exit state->sys_exit
#define sys_sleep state->sys_sleep
