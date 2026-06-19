{% if challenge.syscalls_allowed %}
  scmp_filter_ctx ctx;

  {% if challenge.seccomp_default_kill %}
    {{ "Restricting system calls (default: kill)." | layout_text }}
    ctx = seccomp_init(SCMP_ACT_KILL);
    {% for syscall in challenge.syscalls_allowed %}
      printf("Allowing syscall: %s (number %i).\n", "{{ syscall }}", SCMP_SYS({{ syscall }}));
      assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS({{ syscall }}), 0) == 0);
    {% endfor %}

  {% else %}
    {{ "Restricting system calls (default: allow)." | layout_text }}
    ctx = seccomp_init(SCMP_ACT_ALLOW);
    for (int i = 0; i < 512; i++) {
      switch (i) {
        {% for syscall in challenge.syscalls_allowed %}
          case SCMP_SYS({{ syscall }}):
            printf("Allowing syscall: %s (number %i).\n", "{{ syscall }}", SCMP_SYS({{ syscall }}));
            continue;
        {% endfor %}
      }
      assert(seccomp_rule_add(ctx, SCMP_ACT_KILL, i, 0) == 0);
    }
  {% endif %}

  {% if challenge.seccomp_add_arch_x86 %}
    {{ "Adding architecture to seccomp filter: x86_32." | layout_text }}
    seccomp_arch_add(ctx, SCMP_ARCH_X86);
  {% endif %}
{% endif %}
