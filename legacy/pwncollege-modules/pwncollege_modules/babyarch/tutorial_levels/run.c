{% extends "base/base.c" %}

{% block includes %}
#include <sys/ptrace.h>
#include <sys/user.h>
#include <unistd.h>
#include <string.h>
#include <semaphore.h>
#include <time.h>
#include <inttypes.h>
#include <sched.h>
#include <fcntl.h>
#include <stdbool.h>
#include <assert.h>
#include <sys/sysinfo.h>

#include <x86intrin.h>


{% endblock %}

{% block globals %}
// control page + 256 signal pages 
{% if challenge.speculative %}
  // Need extra pages to train branch predictor
  // Cannot use index zero
  #define SHM_SIZE 0x1000 * (256 + 4)
{% else %}
  #define SHM_SIZE 0x1000 * (256 + 1)
{% endif %}
#define unlikely(x) __builtin_expect((x),0)

const long long int mmap_addr = 0x1337000;

{% include "babyarch/tutorial_levels/ptrace_inject.c" %}
{% include "babyarch/tutorial_levels/spec_funcs.c" %}
{% include "babyarch/tutorial_levels/simp_funcs.c" %}
{% endblock %}

{% block main %}
  pid_t exploit_pid = {0};
  char exploit_path[300];
  char *shared_memory_base;
  int local_shm_fd, remote_shm_fd;
  struct user_regs_struct registers;

  read_flag_to_global(0);

  //
  // Massive helptext blurbs
  //
  puts("This challenge will inject a region of shared memory into the binary specified via argv[1].");
  puts("Please pass your executable's path as the first argument.\n");
  puts(" ");
  printf("This shared memory region will be accessible in your binary memory at address: %p.\n", mmap_addr);
  printf("This means you can access shared_memory_base (in the code below) at %p in your binary.", mmap_addr);
  puts("You DO NOT need to call mmap.  Assume this memory is mapped in your code before main is even");
  puts("called.");
  puts(" ");
  {% if challenge.task == "parseOnePage" or challenge.task == "parseMultiPage" %}
    puts("This challenge will perform a timing sidechannel attack against itself!");
    puts("It can access a single byte of the flag in the challenge's memory.");
    puts("However, the flag bytes are not accessible by your code!");
    puts(" ");
    puts("You can control which byte of the flag is read via the injected shared memory.");
    puts("This flag byte value will influence which page of memory is accessed as shown in the code");
    puts("below.");
    puts(" ");
    puts("This challenge will then measure memory access times at the beginning of each page");
    puts("and make this data available to you via shared memory.");
    puts("Use this information to determine which index is in the CPU cache!");
    puts("Hint: Cached memory addresses have noticeable faster access times. This information can be");
    puts("used as a sidechannel to reveal the flag byte's value.");
    puts(" ");
    puts("This challenge will execute the following code after launching your challenge binary.");
    puts("Note that the challenge binary will be blocked on sem_wait and unable to continue execution.");
    puts("You can influence the binary's behavior by calling sem_post on this semaphore from your code.");
    puts("----------------");
    print_fake_init();
    puts("char *ptr;");
    puts("char buf;");
    puts("char leak;");
    puts("int status;");
    puts("puts(\"Waiting..\");");
    puts("while (waitpid(exploit_pid, &status, WNOHANG) != exploit_pid) {");
    puts("  sem_wait(sem);");
    puts("  // Immediately after will be an index into the flag value");
    puts("  int *index = (int *) (sem + 1);");
    puts(" ");
    puts("  uint64_t timing_data[255];");
    puts(" ");
    puts("  flush_cache();");
    puts(" ");
    puts("  leak = flag_val[*index];");
    puts("  ptr = shared_memory_base + 0x1000 + 0x1000 * (int) leak;");
    puts("  buf = *ptr;");
    puts(" ");
    puts("  get_timing_data(index, sem, timing_data);");
    puts(" ");
    {% if challenge.task == "parseOnePage" %}
      puts("  // Write the timing data to the second page of shared memory");
      puts("  for (int i = 0; i < 256; i++) {");
      puts("    uint64_t *page = (uint64_t *) (shared_memory_base + 0x1000)");
      puts("    page[i] = timing_data[i]");
      puts("  }");
    {% endif %}
    {% if challenge.task == "parseMultiPage" %}
      puts("  // Write the timing data to the respective page of memory");
      puts("  for (int i = 0; i < 256; i++) {");
      puts("    uint64_t *page = (uint64_t *) (shared_memory_base + 0x1000 + 0x1000 * i);");
      puts("    *page = timing_data[i];");
      puts("  }");
    {% endif %}
    puts("}");
    puts("----------------");
  {% endif %}

  {% if challenge.task == "measureTiming" or challenge.task == "all" %}
    {% if challenge.task == "measureTiming" %}
      puts("This challenge is vulnerable to a CPU cache timing sidechannel attack!");
      puts("It can access a single byte of the flag in the challenge's memory.");
      puts("However, the flag bytes are not accessible by your code!");
      puts(" ");
      puts("You can control which byte of the flag is access via the injected shared memory.");
      puts(" ");
      puts("This challenge DOES NOT write the timing data to memory.  Instead, you must measure");
      puts("access times yourself across the shared memory.  The challenge binary is flushing the CPU cache ");
      puts("and performing a single access each time the semaphore is incremented (via sem_post).  Take");
      puts("advantage of this to leak the flag!");
      puts(" ");
    {% endif %}
    puts("This challenge will execute the following code after launching your challenge binary.");
    puts("----------------");
    print_fake_init();
    puts("char *ptr;");
    puts("char buf;");
    puts("char leak;");
    puts("int status;");
    puts(" ");
    {% if challenge.flush_cache == True %}
      puts("flush_cache();");
      puts(" ");
    {% endif %}
    puts("while (waitpid(exploit_pid, &status, WNOHANG) != exploit_pid) {");
    puts("  sem_wait(sem);");
    {% if challenge.speculative %}
      puts("  if (unlikely((float)*index / (float)257 > 1)) {");
      puts("    leak = flag_val[*index];");
      puts("    ptr = shared_memory_base + 0x1000 + 0x1000 * (int) leak; ");
      puts("    buf = *ptr;");
      puts("  }");
    {% else %}
      puts("  leak = flag_val[*index];");
      puts("  ptr = shared_memory_base + 0x1000 + 0x1000 * (int) leak; ");
      puts("  buf = *ptr;");
    {% endif %}
    puts("}");
    puts("----------------");
  {% endif %}

  if (argc < 2) {
    puts("ERROR: argc < 2!");
    return 1;
  }

  //
  // Injection insanity
  //
  strncpy(exploit_path, argv[1], 299);
  exploit_path[299] = '\x00';

  char *args[] = {exploit_path, NULL};

  local_shm_fd = make_shared_page(&shared_memory_base);

  // Let's not have everyone pinned on the same cpu
  // TODO: Hardcoded core count - nproc lies?
  int rand = (int) time(NULL) % 13;
  pin_cpu(rand);
  printf("Pinning processes to CPU %d\n", rand);

  exploit_pid = fork();

  if (!exploit_pid) {
    ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    execv(exploit_path, args);
    return 0; // never encountered
  }
  printf("Launching your code as PID: %d!\n", exploit_pid);
  puts("----------------");
  wait(NULL);
  
  // Child is blocked for us to continue
  remote_shm_fd = inject_open_shm(exploit_pid);
  inject_mmap(exploit_pid, remote_shm_fd);
  inject_drop_privs(exploit_pid);
  
  sem_t *sem = (sem_t *) shared_memory_base;
  sem_init(sem, 1, 0);

  int *index = (int *) (sem + 1);
  *index = 0;

  ptrace_detatch(exploit_pid);

  //
  // Action occurs HERE
  //

  {% if challenge.task == "parseOnePage" or challenge.task == "parseMultiPage" %}
    char *ptr;
    char buf;
    char leak;
    int status;
    puts("Waiting..");
    while (waitpid(exploit_pid, &status, WNOHANG) != exploit_pid) {
      sem_wait(sem);
      // Immediately after will be an index into the flag value
      int *index = (int *) (sem + 1);
  
  
      uint64_t timing_data[255];  

      flush_cache();

      leak = flag_val[*index];
      ptr = shared_memory_base + 0x1000 + 0x1000 * (int) leak; 
      buf = *ptr;

      get_timing_data(index, sem, timing_data);

      {% if challenge.task == "parseOnePage" %}
        // Write the timing data to the second page of shared memory
        for (int i = 0; i < 256; i++) {
          uint64_t *page = (uint64_t *) (shared_memory_base + 0x1000);
          page[i] = timing_data[i];
        }
      {% endif %}
  
      {% if challenge.task == "parseMultiPage" %}
        // Write the timing data to the respective page of memory
        for (int i = 0; i < 256; i++) {
          uint64_t *page = (uint64_t *) (shared_memory_base + 0x1000 + 0x1000 * i);
          *page = timing_data[i];
        }
      {% endif %}
    }
  {% endif %}

  {% if challenge.task=="all" or challenge.task == "measureTiming" %}
    char *ptr;
    char buf;
    char leak;
    int status;



    while (waitpid(exploit_pid, &status, WNOHANG) != exploit_pid) {
      sem_wait(sem);

      {% if challenge.flush_cache == True %}
        flush_cache();
      {% endif %}

      {% if challenge.speculative %}
        if (unlikely((float)*index / (float)257 > 1)) {
      {% endif %}
      leak = flag_val[*index];
      ptr = shared_memory_base + 0x1000 + 0x1000 * (int) leak; 
      buf = *ptr;
      {% if challenge.speculative %}
	}
      {% endif %}
    }
  {% endif %}

  // Cleanup and bail
  shm_unlink("/pwncollege");
{% endblock %}
