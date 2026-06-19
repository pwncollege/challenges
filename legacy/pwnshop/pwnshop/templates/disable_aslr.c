
void __attribute__((constructor)) disable_aslr(int argc, char **argv, char **envp)
{
  int current_personality = personality(0xffffffff);
  assert(current_personality != -1);
  if ((current_personality & ADDR_NO_RANDOMIZE) == 0) {
    assert(personality(current_personality | ADDR_NO_RANDOMIZE) != -1);
    {% if challenge.desuid %}
      fprintf(stderr, "NOTE: This program can only be launched ONCE. You will need to\nrestart your container to launch this program again.\n");
      chmod("/proc/self/exe", 0755);
    {% else %}
      assert(prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != -1);
    {% endif %}
    execve("/proc/self/exe", argv, envp);
  }
}
