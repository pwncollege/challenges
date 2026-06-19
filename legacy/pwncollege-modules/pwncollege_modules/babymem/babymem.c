{% extends "base/base.c" %}

{% set win_name = "win" if not challenge.win_function_authed else "win_authed" %}

{% block includes %}
  {% if challenge.syscalls_allowed %}
    #include <seccomp.h>
  {% endif %}

  {% if walkthrough %}
    {% include "stack_recon.c" %}

    {% if challenge.shellcode_size %}
      {% include "disassemble.c" %}
    {% endif %}
  {% endif %}
{% endblock %}

{% block globals %}
  {% if challenge.verify_flag %}
    int verify_flag()
    {
      struct {
        char padding[{{ challenge.flag_padding }}];
        char flag_buffer[256];
      } data;

      read(open("/flag", 0), data.flag_buffer, 256);

      {% if walkthrough %}
        {% filter layout_text %}
          This challenge reads the flag file to verify it.
          Do you think this might leave traces of the flag around afterwards?
        {% endfilter %}
        printf("The flag was read into address %p.\n\n", data.flag_buffer);
      {% endif %}
    }
  {% endif %}

  {% if challenge.shellcode_size %}
    void *shellcode;
    size_t shellcode_size;
  {% endif %}
{% endblock %}

{% block main %}
  char crash_resistance[0x1000];
  {% if challenge.verify_flag %}
    verify_flag();
  {% endif %}
{% endblock %}

{% block challenge_function %}
  {% if not challenge.mmap_overflow %}
    struct {
      char input[{{ challenge.input_size }}];
      {% if challenge.flag_by_input %}
        char flag[256];
      {% endif %}
      {% if challenge.win_variable %}
        int win_variable;
      {% endif %}
      {% if challenge.lose_variable %}
        int lose_variable;
      {% endif %}
      {% if challenge.backdoor_cookie %}
        unsigned long backdoor_cookie;
      {% endif %}
      {% if challenge.multi_read %}
        int num_bytes_read;
      {% endif %}
      {% if challenge.syscalls_allowed %}
        int syscalls_allowed[{{ challenge.syscalls_allowed | length }}];
      {% endif %}
    } data {% if not challenge.uninitialized_input %} = {0} {% endif %};
    {% set input_addr = "&data.input" %}
    {% if challenge.flag_by_input %}
      char *flag = &data.flag;
    {% endif %}
    {% if challenge.win_variable %}
      {% set winvar_addr = "&data.win_variable" %}
      {% set winvar_value = "data.win_variable" %}
    {% endif %}
    {% if challenge.multi_read %}
      int *num_bytes_read = &data.num_bytes_read;
    {% endif %}
    {% if challenge.syscalls_allowed %}
      int *syscalls_allowed = &data.syscalls_allowed;
    {% endif %}
  {% endif %}

  {{ challenge.size_type }} size = 0;

  {% if challenge.syscalls_allowed %}
    {% for syscall in challenge.syscalls_allowed %}
      syscalls_allowed[{{ loop.index0 }}] = SCMP_SYS({{ syscall }});
    {% endfor %}
  {% endif %}

  {% if walkthrough %}
    puts("The challenge() function has just been launched!");

    {% if challenge.uninitialized_input %}
      puts("However... An important initialization step was missed.");
      puts("Use this to your advantage!");
      puts("");
    {% endif %}

    {% if not challenge.mmap_overflow %}
      GET_FRAME_WORDS(sz_, sp_, bp_, rp_);
      puts("Before we do anything, let's take a look at challenge()'s stack frame:");
      DUMP_STACK(sp_, sz_);
      printf("Our stack pointer points to %p, and our base pointer points to %p.\n", sp_, bp_);
      printf("This means that we have (decimal) %d 8-byte words in our stack frame,\n", sz_);
      printf("including the saved base pointer and the saved return address, for a\n");
      printf("total of %d bytes.\n", sz_ * 8);
      printf("The input buffer begins at %p, partway through the stack frame,\n", &data.input);
      printf("(\"above\" it in the stack are other local variables used by the function).\n");
      printf("Your input will be read into this buffer.\n");
      printf("The buffer is %d bytes long, but the program will let you provide an arbitrarily\n", {{ challenge.input_size }});
      printf("large input length, and thus overflow the buffer.\n\n");

    {% elif challenge.mmap_overflow %}
      puts("This challenge stores your input buffer in an mmapped page of memory!");
      {% if challenge.win_variable %}
        puts("It also stores the \"win\" variable in an mmapped page of memory.");
      {% endif %}
    {% endif %}
  {% endif %}

  {% if challenge.mmap_overflow %}
    {
      void *data = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0);
      {% if walkthrough %}
        printf("Called mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0) = %p\n", data);
      {% endif %}
    }
    {% if challenge.win_variable %}
      {% if walkthrough %}
        printf("Memory mapping the win variable...\n");
      {% endif %}
      int *win_variable = mmap(0, sizeof(int), PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0);
      {% set winvar_addr = "win_variable" %}
      {% set winvar_value = "*win_variable" %}
      {% if walkthrough %}
        printf("Called mmap(0, sizeof(int), PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0) = %p\n", win_variable);
      {% endif %}
    {% endif %}
    {% if challenge.flag_by_input %}
      {% if walkthrough %}
        printf("In this level, the flag will be loaded into memory.\n");
        printf("However, at no point will this program actually print the buffer storing the flag.\n");
        printf("Mapping memory for the flag...\n");
      {% endif %}
      void *flag = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0);
      int flag_fd = open("/flag", O_RDONLY);
      read(flag_fd, flag, 1024);
      close(flag_fd);
      {% if walkthrough %}
        printf("Called mmap(0, 0x1000, 4, MAP_SHARED, open(\"/flag\", 0), 0) = %p\n", flag);
      {% endif %}
    {% endif %}
    for (int i = 0; i < {{ challenge.mmap_padding }}; i++) {
      void *data = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0);
      {% if walkthrough %}
        printf("Called mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0) = %p\n", data);
      {% endif %}
    }
    {% if walkthrough %}
      printf("Memory mapping the input buffer...\n");
    {% endif %}
    char *input = mmap(0, {{ challenge.input_size }}, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0);
    {% set input_addr = "input" %}
    {% if walkthrough %}
      printf("Called mmap(0, {{ challenge.input_size }}, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0) = %p\n", input);
    {% endif %}
  {% endif %}

  {% if challenge.flag_by_input and not challenge.mmap_overflow %}
    {% if walkthrough %}
      printf("In this level, the flag will be loaded into memory.\n");
      printf("However, at no point will this program actually print the buffer storing the flag.\n");
    {% endif %}
    read(open("/flag", 0), flag, 256);
  {% endif %}

  {% if walkthrough %}
    {% if challenge.win_variable %}
      printf("In this level, there is a \"win\" variable.\n");
      printf("By default, the value of this variable is zero.\n");
      {% if challenge.win_value is none %}
      printf("However, when this variable is non-zero, the flag will be printed.\n");
      printf("You can make this variable be non-zero by overflowing the input buffer.\n");
      {% else %}
      printf("However, if you can set variable to {{ '0x%08x'%challenge.win_value }}, the flag will be printed.\n");
      printf("You can change this variable by overflowing the input buffer, but keep endianness in mind!\n");
      {% endif %}
      printf("The \"win\" variable is stored at %p, %d bytes after the start of your input buffer.\n\n", {{winvar_addr}}, ((unsigned long) {{winvar_addr}}) - ((unsigned long) {{input_addr}}));

    {% elif challenge.win_function %}
      printf("In this level, there is no \"win\" variable.\n");
      printf("You will need to force the program to execute the {{ win_name }}() function\n");
      printf("by directly overflowing into the stored return address back to main,\n");
      printf("which is stored at %p, %d bytes after the start of your input buffer.\n", rp_, rp_ - (unsigned long) {{input_addr}});
      printf("That means that you will need to input at least %d bytes (%d to fill the buffer,\n", rp_ + 8 - (unsigned long) {{input_addr}}, {{ challenge.input_size }});
      printf("%d to fill other stuff stored between the buffer and the return address,\n", rp_ - (unsigned long) {{input_addr}} - {{ challenge.input_size }});
      printf("and 8 that will overwrite the return address).\n\n");
    {% endif %}

    {% if challenge.lose_variable %}
      {{ "\nBut be careful! There is also a LOSE variable. If this variable ends up non-zero, the program will terminate and you will not get the flag. Be careful not to overwrite this variable." | layout_text }}
      printf("The \"lose\" variable is stored at %p, %d bytes after the start of your input buffer.\n\n", &data.lose_variable, ((unsigned long) &data.lose_variable) - ((unsigned long) {{input_addr}}));
    {% endif %}

    {% if (challenge.CANARY is false) or (challenge.PIE is false) or (challenge.disable_aslr is true) or (challenge.EXEC_STACK is true) %}
      puts("We have disabled the following standard memory corruption mitigations for this challenge:");
      {% if challenge.CANARY is false %}
        puts("- the canary is disabled, otherwise you would corrupt it before");
        puts("overwriting the return address, and the program would abort.");
      {% endif %}
      {% if challenge.PIE is false %}
        puts("- the binary is *not* position independent. This means that it will be");
        puts("located at the same spot every time it is run, which means that by");
        puts("analyzing the binary (using objdump or reading this output), you can");
        puts("know the exact value that you need to overwrite the return address with.\n");
      {% endif %}
      {% if challenge.disable_aslr is true %}
        puts("- the binary will disable aslr. This means that everything in memory will be");
        puts("located at the same spot every time it is run, which means that by");
        puts("analyzing the binary (using objdump or reading this output), you can");
        puts("know the exact value that you need to overwrite the return address with.");
        puts("Furthermore, you know the absolute address of everything on the stack.\n");
      {% endif %}
      {% if challenge.EXEC_STACK is true %}
        puts("- the stack is executable. This means that if the stack contains shellcode");
        puts("and you overwrite the return address with the address of that shellcode, it will execute.\n");
      {% endif %}
    {% endif %}

    {% if challenge.CANARY and not challenge.mmap_overflow %}
      FIND_CANARY(cp_, cv_, bp_);
    {% endif %}

    {% if challenge.fork_server and challenge.CANARY %}
      puts("While canaries are enabled, this networked program forks.");
      puts("What is important to note is that the canary does not get re-randomized on fork.\n");

      puts("When data that you are overflowing into is critical (i.e., if you screw it up");
      puts("the program crashes), but also static across executions, you can brute-force");
      puts("it byte by byte over many attempts.\n");

      puts("So, let's brute-force the canary!");
      puts("If this is your first time running this program, all you know so far is that");
      puts("the canary has a 0 as its left-most byte.");
      puts("You should proceed like this:\n");

      printf("- First, you should try overflowing just the null byte of the canary, for\n");
      printf("  practice. The canary starts at %p, which is %d bytes after the\n", cp_, cp_ - ((unsigned long) {{input_addr}}));
      printf("  start of your buffer. Thus, you should provide %d characters followed\n", cp_ - ((unsigned long) {{input_addr}}));
      printf("  by a NULL byte, make sure the canary check passes, then try a non-NULL\n");
      printf("  byte and make sure the canary check fails. This will confirm the offsets.\n");
      printf("- Next try each possible value for just the next byte. One of them (the same\n");
      printf("  as whatever was there in memory already) will keep the canary intact, and\n");
      printf("  when the canary check succeeds, you know you have found the correct one.\n");
      printf("- Go on to the next byte, leak it the same way, and so on, until you have\n");
      printf("  the whole canary.\n\n");

      printf("You will likely want to script this process! Each byte might take up to 256\n");
      printf("tries to guess..\n\n");
    {% endif %}

    {% if challenge.multi_read and challenge.CANARY %}
      printf("While canaries are enabled, this program reads your input 1 byte at a time,\n");
      printf("tracking how many bytes have been read and the offset from your input buffer\n");
      printf("to read the byte to using a local variable on the stack.\n");
      printf("The code for doing this looks something like:\n");
      printf("    while (n < size) {\n");
      printf("      n += read(0, input + n, 1);\n");
      printf("    }\n");
      printf("As it turns out, you can use this local variable `n` to jump over the canary.\n");
      printf("Your input buffer is stored at %p, and this local variable `n`\n", {{input_addr}});
      printf("is stored %d bytes after it at %p.\n\n", ((unsigned long) num_bytes_read) - ((unsigned long) {{input_addr}}), num_bytes_read);

      printf("When you overwrite `n`, you will change the program's understanding of\n");
      printf("how many bytes it has read in so far, and when it runs `read(0, input + n, 1)`\n");
      printf("again, it will read into an offset that you control.\n");
      printf("This will allow you to reposition the write *after* the canary, and write\n");
      printf("into the return address!\n\n");

      printf("The payload size is deceptively simple.\n");
      printf("You don't have to think about how many bytes you will end up skipping:\n");
      printf("with the while loop described above, the payload size marks the\n");
      printf("*right-most* byte that will be read into.\n");
      printf("As far as this challenge is concerned, there is no difference between bytes\n");
      printf("\"skipped\" by fiddling with `n` and bytes read in normally: the values\n");
      printf("of `n` and `size` are all that matters to determine when to stop reading,\n");
      printf("*not* the number of bytes actually read in.\n\n");

      printf("That being said, you *do* need to be careful on the sending side: don't send\n");
      printf("the bytes that you're effectively skipping!\n\n");
    {% endif %}
  {% endif %}

  {% if challenge.shellcode_size %}
    {% include "babyshell/alloc_shellcode.c" %}

    {{ "Reading {} bytes of shellcode from stdin.".format(hex(challenge.shellcode_size)) | layout_text }}
    shellcode_size = read(0, shellcode, {{ hex(challenge.shellcode_size) }});
    assert(shellcode_size > 0);

    {% if walkthrough %}
      {{ "This challenge has loaded the following shellcode:" | layout_text }}
      print_disassembly(shellcode, shellcode_size);
      {{ "" | layout_text }}
    {% endif %}

    puts("Press enter to continue!");
    getchar();
  {% endif %}

  {% if challenge.multiple_records %}
    unsigned int record_num;
    unsigned int record_size;
    {% if walkthrough %}
      puts("This challenge will let you send multiple payload records concatenated together.");
      puts("It will make sure that the total payload size fits in the allocated buffer");
      puts("on the stack. Can you send a carefully crafted input to break this calculation?");
    {% endif %}
    printf("Number of payload records to send: ");
    scanf("%u", &record_num);
    assert(record_num > 0);
    printf("Size of each payload record: ");
    scanf("%u", &record_size);
    assert(record_size > 0);
    assert(record_size * record_num <= {{ challenge.input_size }});
    size = record_num;
    size *= record_size;
    {% if walkthrough %}
      printf("Computed total payload size: {{challenge.size_fmt}}\n", size);
    {% endif %}

  {% elif challenge.payload_size %}
    size = {{ challenge.payload_size }};
  {% else %}
    printf("Payload size: ");
    scanf("{{ challenge.size_fmt }}", &size);
  {% endif %}

  {% if challenge.size_check %}
    {% if walkthrough %}
      puts("This challenge is more careful: it will check to make sure you");
      puts("don't want to provide so much data that the input buffer will");
      puts("overflow. But recall twos compliment, look at how the check is");
      puts("implemented, and try to beat it!");
    {% endif %}
    if (size > {{ challenge.input_size }}) {
      puts("Provided size is too large!");
      exit(1);
    }
    {% if walkthrough %}
      puts("You made it past the check! Because the read() call will interpret");
      puts("your size differently than the check above, the resulting read will");
      puts("be unstable and might fail. You will likely have to try this several");
      puts("times before your input is actually read.");
    {% endif %}
  {% endif %}

  {% if walkthrough %}
    printf("You have chosen to send {{ challenge.size_fmt }} bytes of input!\n", size);
    printf("This will allow you to write from %p (the start of the input buffer)\n", {{input_addr}});
    printf("right up to (but not including) %p (which is %d bytes beyond the end of the buffer).\n", size + (unsigned long) {{input_addr}}, size - {{ challenge.input_size }});

    {% if challenge.win_function and not challenge.win_variable %}
      printf("Of these, you will overwrite %d bytes into the return address.\n", (long)((unsigned long) {{input_addr}} + size - rp_));
      printf("If that number is greater than 8, you will overwrite the entire return address.\n\n");

      {% if challenge.win_function_authed %}
        puts("One caveat in this challenge is that the {{ win_name }}() function must first auth:");
        puts("it only lets you win if you provide it with the argument 0x1337.");
        puts("Speifically, the {{ win_name }}() function looks something like:");
        puts("    void {{ win_name }}(int token)");
        puts("    {");
        puts("      if (token != 0x1337) return;");
        puts("      puts(\"You win! Here is your flag: \");");
        puts("      sendfile(1, open(\"/flag\", 0), 0, 256);");
        puts("      puts(\"\");");
        puts("    }");
        puts("");

        printf("So how do you pass the check? There *is* a way, and we will cover it later,\n");
        printf("but for now, we will simply bypass it! You can overwrite the return address\n");
        printf("with *any* value (as long as it points to executable code), not just the start\n");
        printf("of functions. Let's overwrite past the token check in win!\n\n");

        printf("To do this, we will need to analyze the program with objdump, identify where\n");
        printf("the check is in the {{ win_name }}() function, find the address right after the check,\n");
        printf("and write that address over the saved return address.\n\n");

        printf("Go ahead and find this address now. When you're ready, input a buffer overflow\n");
        printf("that will overwrite the saved return address (at %p, %d bytes into the buffer)\n", rp_, rp_ - (unsigned long){{input_addr}});
        printf("with the correct value.\n\n");

      {% else %}
        printf("You will want to overwrite the return value from challenge()\n");
        printf("(located at %p, %d bytes past the start of the input buffer)\n", rp_, rp_ - (unsigned long) {{input_addr}});
        printf("with %p, which is the address of the {{ win_name }}() function.\n", win);
        printf("This will cause challenge() to return directly into the {{ win_name }}() function,\n");
        printf("which will in turn give you the flag.\n");
        printf("Keep in mind that you will need to write the address of the {{ win_name }}() function\n");
        printf("in little-endian (bytes backwards) so that it is interpreted properly.\n\n");
      {% endif %}
    {% endif %}
  {% endif %}

  {% if challenge.string_confusion_input %}
    {% if walkthrough %}
      puts("This challenge is careful about reading your input: it will allocate a correctly-sized temporary");
      puts("buffer on the heap, and then copy the data over to the stack. Can you figure out a way to fool");
      puts("this technique and cause an overflow?");
    {% endif %}
    char *tmp_input = malloc(size);
    assert(tmp_input != 0);
    printf("Send your payload (up to {{ challenge.size_fmt }} bytes)!\n", size);
    int received = read(0, tmp_input, ({{ challenge.size_cast }}) size);
    {% if walkthrough %}
      puts("Checking length of received string...");
    {% endif %}
    size_t string_length = strlen(tmp_input);
    assert(string_length < {{ challenge.input_size }});
    {% if walkthrough %}
      printf("Passed! We should have enough space for all %d bytes of it on the stack. Copying all %d received bytes!\n", string_length, received);
    {% endif %}
    memcpy({{input_addr}}, tmp_input, received);

  {% elif challenge.multi_read %}
    printf("Send your payload (up to {{ challenge.size_fmt }} bytes)!\n", size);
    while (*num_bytes_read < size) {
      {% if walkthrough %}
        printf("About to read 1 byte to %p, this is %d bytes away from the start of the input buffer.\n", {{input_addr}} + *num_bytes_read, *num_bytes_read);
      {% endif %}
      *num_bytes_read += read(0, {{input_addr}} + *num_bytes_read, 1);
    }
    int received = *num_bytes_read;

  {% else %}
    printf("Send your payload (up to {{ challenge.size_fmt }} bytes)!\n", size);
    int received = read(0, {{input_addr}}, ({{ challenge.size_cast }}) size);
  {% endif %}

  if (received < 0) {
    printf("ERROR: Failed to read input -- %s!\n", strerror(errno));
    exit(1);
  }

  {% if walkthrough %}
    printf("You sent %d bytes!\n", received);

    {% if challenge.dump_final_stack %}
      printf("Let's see what happened with the stack:\n\n");
      DUMP_STACK(sp_, sz_);
    {% endif %}

    printf("The program's memory status:\n");
    printf("- the input buffer starts at %p\n", {{input_addr}});
    {% if not challenge.mmap_overflow %}
      printf("- the saved frame pointer (of main) is at %p\n", bp_);
      printf("- the saved return address (previously to main) is at %p\n", rp_);
      printf("- the saved return address is now pointing to %p.\n", *(unsigned long*)(rp_));
      {% if challenge.CANARY %}
        printf("- the canary is stored at %p.\n", cp_);
        printf("- the canary value is now %p.\n", *(unsigned long*)(cp_));
      {% endif %}
    {% endif %}
    {% if challenge.flag_by_input %}
      printf("- the address of the flag is %p.\n", flag);
    {% endif %}
    {% if challenge.win_variable %}
      printf("- the address of the win variable is %p.\n", {{winvar_addr}});
      printf("- the value of the win variable is 0x%x.\n", {{winvar_value}});
    {% endif %}
    {% if challenge.lose_variable %}
      printf("- the address of the lose variable is %p.\n", &data.lose_variable);
      printf("- the value of the lose variable is 0x%x.\n", data.lose_variable);
    {% endif %}
    {% if challenge.multi_read %}
      printf("- the address of the number of bytes read counter and read offset is %p.\n", num_bytes_read);
    {% endif %}
    {% if challenge.win_function and not challenge.win_variable %}
      printf("- the address of {{ win_name }}() is %p.\n", {{ win_name }});
    {% endif %}
    printf("\n");

    {% if challenge.win_function and not challenge.win_variable %}
      printf("If you have managed to overwrite the return address with the correct value,\n");
      printf("challenge() will jump straight to {{ win_name }}() when it returns.\n");
      printf("Let's try it now!\n\n", 0);
    {% endif %}

    {% if challenge.win_function and not challenge.win_variable and challenge.PIE %}
      if (received + ((unsigned long) {{input_addr}}) > rp_ + 2) {
        puts("WARNING: You sent in too much data, and overwrote more than two bytes of the address.");
        puts("         This can still work, because I told you the correct address to use for");
        puts("         this execution, but you should not rely on that information.");
        puts("         You can solve this challenge by only overwriting two bytes!");
        puts("         ");
      }
    {% endif %}
  {% endif %}

  {% if challenge.lose_variable %}
    if (data.lose_variable) {
      puts("Lose variable is set! Quitting!");
      exit(1);
    }
  {% endif %}
  {% if challenge.win_variable and challenge.win_value is not none %}
    if ({{winvar_value}} == {{challenge.win_value}}) {
      win();
    }
  {% elif challenge.win_variable %}
    if ({{winvar_value}}) {
      win();
    }
  {% endif %}

  {% if challenge.echo_input %}
    printf("You said: {{challenge.echo_fmt}}\n", {{input_addr}});
  {% endif %}

  {% if challenge.repeat_backdoor %}
    {% if walkthrough %}
      puts("This challenge has a trick hidden in its code. Reverse-engineer the binary right after this puts()");
      puts("call to see the hidden backdoor!");
    {% endif %}
    if (strstr({{input_addr}}, "REPEAT")) {
      puts("Backdoor triggered! Repeating challenge()");
      return challenge(argc, argv, envp);
    }
  {% endif %}

  {% if challenge.conditional_jail %}
    {% if walkthrough %}
      puts("This challenge will, by default, initialize a seccomp filter jail before exiting");
      puts("the challenge function. You will have to reverse engineer the program to");
      puts("understand how to avoid this.");
    {% endif %}
    if (data.backdoor_cookie != {{ challenge.backdoor_cookie }}) {
  {% endif %}

  {% if challenge.syscalls_allowed %}
    scmp_filter_ctx ctx;
    {% if walkthrough %}
      puts("Restricting system calls (default: kill)");
    {% endif %}
    ctx = seccomp_init(SCMP_ACT_KILL);
    for (int i = 0; i < {{ challenge.syscalls_allowed | length }}; i++) {
      {% if walkthrough %}
        printf("Allowing syscall: %s (number %i)\n", seccomp_syscall_resolve_num_arch(SCMP_ARCH_NATIVE, syscalls_allowed[i]), syscalls_allowed[i]);
      {% endif %}
      assert(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscalls_allowed[i], 0) == 0);
    }

    assert(seccomp_load(ctx) == 0);
  {% endif %}

  {% if challenge.conditional_jail %}
    }
    else {
      puts("Jail avoided! Continuing execution.");
    }
  {% endif %}

  puts("Goodbye!");

  {% if challenge.conditional_exit %}
    {% if walkthrough %}
      puts("This challenge will, by default, exit() instead of returning from the");
      puts("challenge function. When a process exit()s, it ceases to exist immediately,");
      puts("and no amount of overwritten return addresses will let you hijack its control");
      puts("flow. You will have to reverse engineer the program to understand how to avoid");
      puts("making this challenge exit(), and allow it to return normally.");
    {% endif %}
    if (data.backdoor_cookie != {{ challenge.backdoor_cookie }}) {
      puts("exit() condition triggered. Exiting!");
      exit(42);
    }
    puts("exit() condition avoided! Continuing execution.");
  {% endif %}

  return 0;
{% endblock %}
