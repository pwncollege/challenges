{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.syscalls_allowed %}
    #include <seccomp.h>
  {% endif %}

  {% if challenge.shellcode %}
    {% include "disassemble.c" %}
  {% endif %}

  {% if challenge.nsroot %}
    #include <sys/syscall.h>
    #include <sys/mount.h>
    #include <dirent.h>
    #include <limits.h>
    #include <sched.h>
  {% endif %}

{% endblock +%}

{% block main %}
  {% if challenge.chroot %}
    {% filter layout_text %}
      This challenge will chroot into a jail in {{ challenge.chroot_path }}.
      You will be able to easily read a fake flag file inside this jail, not the real flag file outside of it.
      If you want the real flag, you must escape.
    {% endfilter %}
  {% endif %}

  {% if challenge.nsroot %}
    {% filter layout_text %}
      This challenge will use mount namespace and pivot_root to put you into a jail in {{ challenge.chroot_path }}.
      You will be able to easily read a fake flag file inside this jail, not the real flag file outside of it.
      If you want the real flag, you must escape.
    {% endfilter %}
  {% endif %}

  {% if challenge.send_file %}
    {{ "The only thing you can do in this challenge is read out one single file, as specified by the first argument to the program (argv[1])." | layout_text }}
  {% endif %}

  {% if challenge.open_file %}
    {{ "You may open a specified file, as given by the first argument to the program (argv[1])." | layout_text }}
  {% endif %}

  {% if challenge.scratch_dir %}
    {% filter layout_text %}
      You may pick a directory (with many restrictions), as given by the first argument to the program (argv[1]).
      This directory will be bind-mounted into your jail.
    {% endfilter %}
  {% endif %}

  {% if challenge.shellcode %}
    {{ "You may upload custom shellcode to do whatever you want." | layout_text }}
  {% endif %}

  {% if challenge.syscalls_allowed %}
    {{ "For extra security, this challenge will only allow certain system calls!" | layout_text }}
  {% endif %}

  {% if challenge.open_file or challenge.send_file or challenge.scratch_dir %}
    assert(argc > 1);
  {% endif %}

  {% if challenge.close_fds %}
    for (int i = 3; i < 10000; i++) close(i);
  {% endif %}

  {% if challenge.open_file %}
    {% if not challenge.allow_flag_path %}
      {{ "Checking to make sure you're not trying to open the flag." | layout_text }}
      assert(strstr(argv[1], "flag") == NULL);
    {% endif %}

    int fd = open(argv[1], O_RDONLY|O_NOFOLLOW);
    if (fd < 0)
      printf("Failed to open the file located at `%s`.\n", argv[1]);
    else
      printf("Successfully opened the file located at `%s`.\n", argv[1]);
  {% endif %}

  {% if challenge.scratch_dir %}
    puts("Checking your data directory path for shenanigans...");
    assert(argv[1][0] == '/');
    assert(strstr(argv[1], ".") == NULL);
    assert(strstr(argv[1], "flag") == NULL);
    assert(strstr(argv[1], "root") == NULL);
    assert(strstr(argv[1], "tmp") == NULL);
    assert(strstr(argv[1], "var") == NULL);
    assert(strstr(argv[1], "run") == NULL);
    assert(strstr(argv[1], "dev") == NULL);
    assert(strstr(argv[1], "fd") == NULL);
    if (strstr(argv[1], "home")) assert(strcmp("/home/hacker", argv[1]) == 0);
    else {
      puts("... to minimize shenanigans, we only support your home dir or a non-writable leaf directory (no subdirs).");
      struct stat statbuf;
      struct dirent *dent;
      char dirpath[1024];
      DIR *dir;

      assert(lstat(argv[1], &statbuf) != -1);
      assert(S_ISDIR(statbuf.st_mode));
      assert(dir = opendir(argv[1]));
      while ((dent = readdir(dir)) != NULL) {
      if (strcmp(dent->d_name, ".") == 0 || strcmp(dent->d_name, "..") == 0) continue;
        snprintf(dirpath, 1024, "%s/%s", argv[1], dent->d_name);
        printf("... making sure %s is not a directory\n", dirpath);
        assert(stat(dirpath, &statbuf) != -1);
        assert(!S_ISDIR(statbuf.st_mode));
      }
      closedir(dir);
    }
  {% endif %}

  {% if challenge.chroot %}
    char jail_path[] = "{{ challenge.chroot_path }}";
    assert(mkdtemp(jail_path) != NULL);

    printf("Creating a jail at `%s`.\n", jail_path);

    assert(chroot(jail_path) == 0);
  {% endif %}

  {% if challenge.nsroot %}
    char new_root[] = "{{ challenge.chroot_path }}";
    char old_root[PATH_MAX];

    puts("Checking that the challenge is running as root (otherwise things will fail)...");
    assert(geteuid() == 0);

    puts("Splitting off into our own mount namespace...");
    assert(unshare(CLONE_NEWNS) != -1);

    // create the new root
    puts("Creating a jail structure!");
    puts("... creating jail root...");
    assert(mkdtemp(new_root) != NULL);
    printf("... created jail root at `%s`.\n", new_root);

    // change the old root (/) to a private mount so that changes aren't propagated to parent mount namespaces
    // (note: rather than doing this propagation, pivot_root will just fail)
    puts("... changing the old / to a private mount so that pivot_root succeeds later.");
    assert(mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != -1);

    puts("... bind-mounting the new root over itself so that it becomes a 'mount point' for pivot_root() later.");
    assert(mount(new_root, new_root, NULL, MS_BIND, NULL) != -1);

    puts("... creating a directory in which pivot_root will put the old root filesystem.");
    snprintf(old_root, sizeof(old_root), "%s/old", new_root);
    assert(mkdir(old_root, 0777) != -1);

    puts("... pivoting the root filesystem!");
    assert(syscall(SYS_pivot_root, new_root, old_root) != -1);

    {% for dir in challenge.mounted_dirs %}
      assert(mkdir("/{{dir}}", 0755) != -1);
      puts("... bind-mounting /{{dir}} into the jail.");
      assert(mount("/old/{{dir}}", "/{{dir}}", NULL, MS_BIND, NULL) != -1);

      {% if challenge.mounted_dirs_ro %}
        puts("... making /{{dir}} read-only...");
        assert(mount(NULL, "/{{dir}}", NULL, MS_REMOUNT|MS_RDONLY|MS_BIND, NULL) != -1);
      {% else %}
        puts("... though the mounts are independent, changes to the files themselves will propagate to the parent namespace!");
      {% endif %}
    {% endfor %}

    {% if challenge.scratch_dir %}
      char dirpath[1024];
      snprintf(dirpath, 1024, "/old%s", argv[1]);
      printf("... bind-mounting (read-only) %s for you into /data in the jail.\n", dirpath);
      assert(mkdir("/data", 0755) != -1);
      assert(mount(dirpath, "/data", NULL, MS_BIND, NULL) != -1);
      assert(mount(NULL, "/data", NULL, MS_REMOUNT|MS_RDONLY|MS_BIND, NULL) != -1);
    {% endif %}

    // let's remove the old root mount
    {% if challenge.unmount_old_root %}
    puts("... unmounting old root directory.");
    assert(umount2("/old", MNT_DETACH) != -1);
    assert(rmdir("/old") != -1);
    {% endif %}

    // make things simpler for everyone to avoid strange behavior with permissions
    setresuid(0, 0, 0);
  {% endif %}

  {% if challenge.chroot or challenge.nsroot %}
    {% if challenge.chdir %}
      {{ "Moving the current working directory into the jail." | layout_text }}
      assert(chdir("/") == 0);
    {% endif %}

    int fffd = open("/flag", O_WRONLY | O_CREAT);
    write(fffd, "{{ challenge.fake_flag }}", {{ challenge.fake_flag | length }});
    close(fffd);
  {% endif %}

  {% if challenge.send_file %}
    printf("Sending the file at `%s` to stdout.\n", argv[1]);
    sendfile(1, open(argv[1], 0), 0, 128);
  {% endif %}

  {% if challenge.shellcode %}
    void *shellcode = mmap((void *)0x1337000, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
    assert(shellcode == (void *)0x1337000);
    printf("Mapped 0x1000 bytes for shellcode at %p!\n", shellcode);

    {{ "Reading 0x1000 bytes of shellcode from stdin." | layout_text }}
    int shellcode_size = read(0, shellcode, 0x1000);

    {{ "This challenge is about to execute the following shellcode:" | layout_text }}
    print_disassembly(shellcode, shellcode_size);
    {{ "" | layout_text }}

    {% include "babyjail/seccomp_init.c" %}

    {{ "Executing shellcode!" | layout_text }}

    {% if challenge.syscalls_allowed %}
    assert(seccomp_load(ctx) == 0);
    {% endif %}

    ((void(*)())shellcode)();
  {% endif %}

  {% if challenge.shell %}
  puts("Executing a shell inside the sandbox! Good luck!");
  assert(execl("/bin/bash", "/bin/bash", "-p", NULL) != -1);
  {% endif %}
{% endblock %}
