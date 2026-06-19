{% if challenge.syscalls_allowed %}
  scmp_filter_ctx ctx;

  {% if challenge.seccomp_default_kill %}
    {{ "Restricting system calls (default: kill)." | layout_text }}
    ctx = seccomp_init(SCMP_ACT_KILL);
    {% for syscall in challenge.syscalls_allowed %}
      printf("Allowing syscall: %s (number %i).\n", "{{ syscall }}", SCMP_SYS({{ syscall }}));
      assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS({{ syscall }}), 0) == 0);
    {% endfor %}
  {% endif %}
{% endif %}
