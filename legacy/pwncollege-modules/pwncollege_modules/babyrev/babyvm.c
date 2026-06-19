#define _GNU_SOURCE 1

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/signal.h>
#include <sys/mman.h>
#include <sys/sendfile.h>
#include <sys/prctl.h>
#include <sys/personality.h>
#include <arpa/inet.h>

{% if challenge.disable_aslr %}
{% include "disable_aslr.c" %}
{% endif %}

{% if walkthrough and challenge.dump_stack %}
{% include "stack_recon.c" %}
{% endif %}

{% if challenge.seed_flag %}
{% include "flag_seed.c" %}
{% endif %}

{% if walkthrough %}
  #define TRACE printf
{% else %}
  #define TRACE(fmt, ...)
{% endif %}

{% include "babyrev/yan85_common.c" %}

{% include "babyrev/yan85_syscall.c" %}

{% if walkthrough %}
  {% include "babyrev/yan85_debug.c" %}
{% endif %}

{% if challenge.interpreted %}
{% include "babyrev/yan85_interpreter.c" %}
{% endif %}

{% if challenge.compiled %}
{% include "babyrev/yan85_jit.c" %}
{% endif %}

{% if challenge.vm_code %}
unsigned char vm_code[] = {
	{{challenge.vm_code}}
};
unsigned int vm_code_length = {{challenge.vm_code_length}};
unsigned char vm_mem[] = {
	{{challenge.vm_mem}}
};
{% endif %}


int main(int argc, char **argv)
{
  printf("[+] Welcome to %s!\n", argv[0]);
  puts("[+] This challenge is an custom emulator. It emulates a completely custom");
  puts("[+] architecture that we call \"Yan85\"! You'll have to understand the");
  puts("[+] emulator to understand the architecture, and you'll have to understand");
  puts("[+] the architecture to understand the code being emulated, and you will");
  puts("[+] have to understand that code to get the flag. Good luck!");

  {% if challenge.direct_interpret_calls %}
  puts("[+]");
  puts("[+] This is an introductory Yan85 level, where we trigger Yan85 architecture");
  puts("[+] operations directly. The parts of Yan85 that are used here is the emulated");
  puts("[+] registers, memory, and system calls.");
  {% else %}
  puts("[+]");
  puts("[+] This level is a full Yan85 emulator. You'll have to reason about yancode,");
  puts("[+] and the implications of how the emulator interprets it!");
  {% endif %}

  {% if challenge.operand_type == "unsigned long long" %}
  puts("[X]");
  puts("[X] Arizona State University is proud to present a NEW version of Yan85:");
  puts("[X] Yan85_64! This is a beta preview of the cutting-edge technology, armed");
  puts("[X] with the latest in security mitigations. Hopefully, we didn't forget to");
  puts("[X] check all the memory accesses properly, though you never know....");
  puts("[X]");
  {% endif %}

  setvbuf(stdout, NULL, _IONBF, 1);
  vmstate_t state = { 0 };
  {% if challenge.rerandomize %}
  puts("[?] This challenge is special! It randomizes the Yan85 VM based on");
  puts("[?] the value of the flag. This means that there is no way for you");
  puts("[?] to know the opcode and argument encodings...");
  puts("[?]");
  puts("[?] Keep in mind that the encoding that you observe in practice mode");
  puts("[?] is going to be different than the actual encoding, because the");
  puts("[?] practice mode flag is different. How will you adapt?");
  puts("[?]");
  puts("[?] Is there maybe a clever side channel you can utilize?");
  rerandomize();
  puts("[?] ... Done! VM is randomized!");
  {% endif %}


  {% if challenge.vm_code %}
  memcpy(state.code, vm_code, vm_code_length);
  memcpy(state.memory, vm_mem, CODE_LENGTH);
  {% elif not challenge.direct_interpret_calls %}
  printf("[!] This time, YOU'RE in control! Please input your yancode: ");
  {% if walkthrough and challenge.no_open %}
  puts("[+] This challenge doesn't allow you to call open via the sys instruction, but luckily,");
  puts("[+] it makes a memory error that will let you accomplish your goals. Good luck!");
  {% endif %}
  read(0, state.code, sizeof(state.code));

  {% if challenge.one_syscall %}
  puts("[!] Are you ready for ultimate Yan85 shellcoding? This challenge only allows you ONE sys instruction!");
  int num_syscalls = 0;
  for (int i = 0; i < CODE_LENGTH; i++) if (state.code[i].op & INST_SYS) num_syscalls++;
  assert(num_syscalls <= 1);
  {% if walkthrough and challenge.mem_first %}
  puts("[+] This might seem impossible, but this challenge makes one memory error that will allow you");
  puts("[+] to execute the system calls you need. The error is what's known as an *intra-frame* overflow:");
  puts("[+] you won't be able to hijack control flow, but you'll be able to mess with the intended logic");
  puts("[+] of the emulator!");
  {% else %}
  puts("[+] Insanely enough, this challenge does not have any memory errors. You'll have to truly");
  puts("[+] understand the Yan85 emulator to solve it! This is reversing + shellcoding at its finest.");
  {% endif %}
  {% endif %}

  {% if walkthrough and challenge.dump_stack %}
  GET_FRAME_WORDS(sz_, sp_, bp_, rp_);
  puts("[!] Let's take a look at the stack before we execute your yancode:");
  DUMP_STACK(sp_, sz_);
  printf("[-] the saved frame pointer (of main) is at %p\n", bp_);
  printf("[-] the saved return address is at %p\n", rp_);
  printf("[-] the saved return address is currently pointing to %p.\n", *(unsigned long*)(rp_));
  {% endif %}

  {% endif %}

  {% if walkthrough %}
  puts("[+]");
  puts("[+] This is a *teaching* challenge, which means that it will output");
  puts("[+] a trace of the Yan85 code as it processes it. The output is here");
  puts("[+] for you to understand what the challenge is doing, and you should use");
  puts("[+] it as a guide to help with your reversing of the code.");
  puts("[+]");
  {% endif %}

  {% if challenge.interpreted %}
  {% if challenge.direct_interpret_calls %}
  execute_program(&state);
  {% else %}
  interpreter_loop(&state);
  {% endif %}
  {% elif challenge.compiled %}
  state.compiled_code = mmap((void *) {{ hex(challenge.jit_code_address) }}, {{ hex(challenge.jit_code_size) }}, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
  void *code_end = emit_program(&state);
  assert(mprotect(state.compiled_code, {{ hex(challenge.jit_code_size) }}, PROT_READ|PROT_EXEC) == 0);
  {% if walkthrough %}
  puts("[!] Your yancode has been JITed! The result is the following x86_64 code:");
  print_disassembly(state.compiled_code, (char*)code_end - (char*)state.compiled_code);
  {% endif %}
  ((void(*)())state.compiled_code)();
  {% endif %}

  {% if not challenge.interpret_forever %}
  puts("[+] Exited interpreter loop! I hope you accomplished what you wanted!");
  {% if walkthrough and challenge.dump_stack %}
  puts("[!] Let's take a look at the stack after your yancode executed:");
  DUMP_STACK(sp_, sz_);
  printf("[-] the saved frame pointer (of main) is at %p\n", bp_);
  printf("[-] the saved return address is at %p\n", rp_);
  printf("[-] the saved return address is now pointing to %p.\n", *(unsigned long*)(rp_));
  {% endif %}
  {% endif %}
}
