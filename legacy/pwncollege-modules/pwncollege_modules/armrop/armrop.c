{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.leak_libc %}
    #include <dlfcn.h>
  {% endif %}

  {% if walkthrough %}
    {% include "stack_recon_aarch64.c" %}
    {% include "disassemble_rop_aarch64.c" %}
  {% endif %}
{% endblock %}

{% block globals %}
  {% if challenge.force_import %}
    void force_import()
    {
      {% for import in challenge.force_import %}
        ((void(*)()){{ import }})();
      {% endfor %}
    }
  {% endif %}

  {% if challenge.free_gadgets %}
    void free_gadgets()
    {
      {% for gadget in challenge.free_gadgets %}
        long long variable_{{ loop.index0 }} = 0x{{ gadget[::-1].hex() }};
      {% endfor %}
    }
  {% endif %}

  {% if challenge.free_gadgets_asm %}
    void free_gadgets_asm()
    {
      {% for asm in challenge.free_gadgets_asm %}
      asm volatile ("{{ asm }}" :  : : );
      {% endfor %}
    }
  {% endif %}  


  {% if challenge.multi_staged_win_function %}
    {% for stage in challenge.multi_staged_win_function %}
      void win_stage_{{ stage }}(int value) {
        {% if challenge.multi_staged_win_function_authed %}
          if (value != {{ stage }}) {
            puts("Error: Incorrect value!");
            return;
          }
        {% endif %}

        char flag[256];
        int fd = open("/flag", 0);
        int size = lseek(fd, 0, SEEK_END) / {{ challenge.multi_staged_win_function | length }} + 1;
        lseek(fd, size * {{ stage - 1 }}, SEEK_SET);
        int count = read(fd, flag, size);
        write(1, flag, count);
        close(fd);
      }
    {% endfor %}
  {% endif %}

  {% if challenge.multi_staged_win_function_real %}
    int last_level = 0;
    {% for stage in challenge.multi_staged_win_function_real %}
      void win_stage_{{ stage }}(int value) {
        {% if challenge.multi_staged_win_function_authed %}
          if (value != {{ stage }}) {
            puts("Error: Incorrect value!");
            return;
          }
        {% endif %}

        char flag[256];
        int fd = open("/flag", 0);
        int size = lseek(fd, 0, SEEK_END) / {{ challenge.multi_staged_win_function | length }} + 1;
        lseek(fd, size * {{ stage - 1 }}, SEEK_SET);
        int count = read(fd, flag, size);
        if (last_level != (value-1))
        {
           return;
        }
        last_level = value;
        write(1, flag, count);
        close(fd);
      }
    {% endfor %}
  {% endif %}


  {% if challenge.bss_read %}
    struct {
      char padding[0x10000];
      char input[{{challenge.read_size}}];
    } data;
  {% endif %}
{% endblock %}

{% block main %}
  char crash_resistance[0x1000];
{% endblock %}

{% block challenge_function %}
  {% if challenge.vuln_pad %}
    asm volatile (".rept 512; nop; .endr");
  {% endif %}

  {% filter layout_text_walkthrough %}
    This challenge reads in some bytes, overflows its stack, and allows you to perform a ROP attack.
    Through this series of challenges, you will become painfully familiar with the concept of Return Oriented Programming!
  {% endfilter %}

  {% if challenge.bss_read %}
    char local_placeholder[8];
    {% set input = "data.input" %}

  {% elif challenge.win_shellcode %}
    struct {
      void *win_addr;
      char input[{{ challenge.input_size }}];
    } data = {0};
    {% set input = "data.input" %}

  {% else %}
    char input[{{ challenge.input_size }}];
    {% set input = "input" %}
  {% endif %}

  {% if walkthrough %}
    GET_FRAME_WORDS(sz_, sp_, bp_, rp_);

    {% if challenge.PIE %}
      {% filter layout_text_walkthrough %}
        PIE is turned on!
        This means that you do not know where any of the gadgets in the main binary are.
        However, you can do a partial overwrite of the saved instruction pointer in order to execute 1 gadget!
        If that saved instruction pointer goes to libc, you will need to ROP from there.
        If that saved instruction pointer goes to the main binary, you will need to ROP from there.
        You may need need to execute your payload several times to account for the randomness introduced.
        This might take anywhere from 0-12 bits of bruteforce depending on the scenario.
      {% endfilter %}
    {% endif %}

    {% if challenge.win_function %}
      printf("In this challenge, there is a win() function.\n");
      printf("win() will open the flag and send its data to stdout; it is at %p.\n", win);
      printf("In order to get the flag, you will need to call this function.\n\n");
    {% endif %}

    {% if challenge.multi_staged_win_function %}
      {% filter layout_text_walkthrough %}
        In this challenge, there are {{ challenge.multi_staged_win_function | length }} stages of win functions.
        The functions are labeled `win_stage_1` through `win_stage_{{ challenge.multi_staged_win_function | length }}`.
        In order to get the flag, you will need to call all of these stages in order.
      {% endfilter %}
    {% endif %}

    {% if challenge.multi_staged_win_function_authed %}
      {% filter layout_text_walkthrough %}
        In addition to calling each function in the right order,
        you must also pass an argument to each of them!
        The argument you pass will be the stage number.
        For instance, `win_stage_1(1)`.
      {% endfilter %}
    {% endif %}

    {% if challenge.win_function or challenge.multi_staged_win_function %}
      printf("You can call a function by directly overflowing into the saved return address,\n");
      printf("which is stored at %p, %d bytes after the start of your input buffer.\n", rp_, rp_ - (unsigned long) {{ input }});
      printf("That means that you will need to input at least %d bytes (%d to fill the buffer,\n", rp_ + 8 - (unsigned long) {{ input }}, {{ challenge.input_size }});
      printf("%d to fill other stuff stored between the buffer and the return address,\n", rp_ - (unsigned long) {{ input }} - {{ challenge.input_size }});
      printf("and 8 that will overwrite the return address).\n");
    {% endif %}

    {% if challenge.win_shellcode %}
      printf("In this challenge, a pointer to the win function is stored on the stack.\n");
      printf("That pointer is stored at %p, %d bytes before your input buffer.\n", &data.win_addr, ((unsigned long) {{ input }}) - ((unsigned long) &data.win_addr));
      printf("If you can pivot the stack to make the next gadget run be that win function, you will get the flag!\n\n");
    {% endif %}

    {% if challenge.hint_libc_leak %}
      puts("This challenge doesn't give you much to work with, so you will have to be resourceful.");
      puts("What you'd really like to know is the address of libc.");
      puts("In order to get the address of libc, you'll have to leak it yourself.");
      puts("An easy way to do this is to do what is known as a `puts(puts)`.");
      puts("The outer `puts` is puts@plt: this will actually invoke puts, thus initiating a leak.");
      puts("The inner `puts` is puts@got: this contains the address of puts in libc.");
      puts("Then you will need to continue executing a new ROP chain with addresses based on that leak.");
      puts("One easy way to do that is to just restart the binary by returning to its entrypoint.");
    {% endif %}

    {% if challenge.bss_read %}
      puts("Previous challenges let you write your ROP chain directly onto the stack.");
      puts("This challenge is not so nice!");
      puts("Your input will be read to the .bss, and only a small part of it will be copied to the stack.");
      puts("You will need to figure out how to use stack pivoting to execute your full ropchain!");
    {% endif %}
  {% endif %}

  {% if challenge.leak_stack %}
    {% if walkthrough %}
      printf("ASLR means that the address of the stack is not known,\n");
      printf("but I will simulate a memory disclosure of it.\n");
      printf("By knowing where the stack is, you can now reference data\n");
      printf("that you write onto the stack.\n");
      printf("Be careful: this data could trip up your ROP chain,\n");
      printf("because it could be interpreted as return addresses.\n");
      printf("You can use gadgets that shift the stack appropriately to avoid that.\n");
    {% endif %}

    printf("[LEAK] Your input buffer is located at: %p.\n\n", {{ input }});
  {% endif %}

  {% if challenge.leak_libc %}
    {% if walkthrough %}
      printf("ASLR means that the address of the libraries is not known,\n");
      printf("but I will simulate a memory disclosure of libc.");
      printf("By knowing where libc is, you can now utilize the HUMONGOUS amount of gadgets\n");
      printf("present in it for your ROP chain.\n");
    {% endif %}

    printf("[LEAK] The address of \"system\" in libc is: %p.\n\n", dlsym(RTLD_NEXT, "system"));
  {% endif %}

  {% if challenge.win_shellcode %}
    data.win_addr = mmap(0, {{ hex(challenge.win_shellcode | length) }}, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, 0, 0);
    memcpy(data.win_addr, "{{ challenge.win_shellcode }}", {{ challenge.win_shellcode | length }});
    assert(mprotect(data.win_addr, {{ hex(challenge.win_shellcode | length) }}, PROT_READ|PROT_EXEC) == 0);

    {% if walkthrough %}
      printf("The win function has just been dynamically constructed at %p.\n", data.win_addr);
    {% endif %}
  {% endif %}

  {% if challenge.arbitrary_read %}
    {% if walkthrough %}
      puts("This will simulate an 8-byte arbitrary read.");
    {% endif %}
    void *address = NULL;
    unsigned long long value;
    printf("Address in hex to read from:\n");
    scanf("%p", &address);
    value = *((unsigned long long *) address);
    printf("[LEAK] *%p = 0x%016llx\n\n", address, value);
  {% endif %}
  int received = read(0, {{ input }}, {{ challenge.read_size }});

  {% if walkthrough %}
    printf("Received %d bytes! This is potentially %d gadgets.\n", received, {% if challenge.bss_read %} received/8 {% else %} (received - (rp_ - (unsigned long) {{ input }})) / 8 {% endif %});
    printf("Let's take a look at your chain! Note that we have no way to verify that the gadgets are executable\n");
    printf("from within this challenge. You will have to do that by yourself.\n");
    {% if challenge.bss_read %}
      print_chain((void *) {{ input }}, received / 8);
    {% else %}
      print_chain((void *) rp_, (received - (rp_ - (unsigned long) {{ input }})) / 8 + 1);
    {% endif %}
  {% endif %}

  {% if challenge.bss_read %}
    unsigned char *bp_;
    asm volatile ("mov %0, rbp" : "=r"(bp_) : : );
    memcpy(bp_+8, {{ input }}, {{challenge.copy_size}});
    {% if walkthrough %}
      printf("Of course, only %d bytes of the above ropchain was copied to the stack!\n", {{challenge.copy_size}});
      printf("Let's take a look at just that part of the chain. To execute the rest, you'll have to pivot the stack!\n");
      print_chain((void *) rp_, {{challenge.copy_size / 8}});
    {% endif %}
  {% endif %}

  puts("Leaving!");

  {% if challenge.vuln_pad %}
    asm volatile (".rept 512; nop; .endr");
  {% endif %}

{% endblock %}
