void __attribute__((constructor)) auto_gdb(int argc, char **argv, char **envp)
{
  char program_path[256] = { 0 };
  char parent_path_symlink[256] = { 0 };
  char parent_path[256] = { 0 };
  char *gdb_argv[256] = { 0 };
  int i;

  snprintf(parent_path_symlink, sizeof(parent_path_symlink), "/proc/%d/exe", getppid());
  readlink(parent_path_symlink, parent_path, sizeof(program_path) - 1);

  if (!strcmp(parent_path, "/usr/bin/gdb"))
      return;

  readlink("/proc/self/exe", program_path, sizeof(program_path) - 1);

  gdb_argv[0] = "/usr/bin/gdb";
  assert(argc < 250);
  for (i = 1; i < argc; i++)
      gdb_argv[i] = argv[i];
  gdb_argv[i++] = "--args";
  gdb_argv[i++] = program_path;
  gdb_argv[i++] = NULL;

  {% filter layout_text %}
    The program is restarting under the control of gdb!
    You can run the program with the gdb command `run`.
  {% endfilter %}

  execve(gdb_argv[0], gdb_argv, envp);
}
