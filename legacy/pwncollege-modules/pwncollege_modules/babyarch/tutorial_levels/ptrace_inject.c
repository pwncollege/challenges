struct memdata {
  long addr;
  long val;
  struct memdata *next;
};

void show_rip_instr(pid_t pid) {
  struct user_regs_struct regs;
    if (ptrace(PTRACE_GETREGS, pid, 0, &regs) == -1) {
      perror("FAILED: ptrace_getregs");
      exit(1);
    }

    long rip_instr = ptrace(PTRACE_PEEKDATA, pid, regs.rip, NULL);
    if (rip_instr == -1) {
      perror("Failed: PTRACE_PEEKDATA");
      exit(1);
    }
    printf("RIP INSTR: %lx\n", rip_instr);
}

void display_registers(struct user_regs_struct *regs) {
	printf("r15: %llx\n", regs->r15);
	printf("r14: %llx\n", regs->r14);
	printf("r13: %llx\n", regs->r13);
	printf("r12: %llx\n", regs->r12);
	printf("rbp: %llx\n", regs->rbp);
	printf("rbx: %llx\n", regs->rbx);
	printf("r11: %llx\n", regs->r11);
	printf("r10: %llx\n", regs->r10);
	printf("r9: %llx\n", regs->r9);
	printf("r8: %llx\n", regs->r8);
	printf("rax: %llx\n", regs->rax);
	printf("rcx: %llx\n", regs->rcx);
	printf("rdx: %llx\n", regs->rdx);
	printf("rsi: %llx\n", regs->rsi);
	printf("rdi: %llx\n", regs->rdi);
	printf("orig_rax: %llx\n", regs->orig_rax);
	printf("rip: %llx\n", regs->rip);
	printf("cs: %llx\n", regs->cs);
	printf("eflags: %llx\n", regs->eflags);
	printf("rsp: %llx\n", regs->rsp);
	printf("ss: %llx\n", regs->ss);
	printf("fs_base: %llx\n", regs->fs_base);
	printf("gs_base: %llx\n", regs->gs_base);
	printf("ds: %llx\n", regs->ds);
	printf("es: %llx\n", regs->es);
	printf("fs: %llx\n", regs->fs);
	printf("gs: %llx\n", regs->gs);
  printf("============================\n\n");
}

void inject_regs(pid_t pid, struct user_regs_struct *regs) {
  if (ptrace(PTRACE_SETREGS, pid, NULL, regs) == -1) {
    perror("Failed: PTRACE_SETREGS");
    exit(1);
  }
}

void ptrace_cont(pid_t pid) {
  if (ptrace(PTRACE_CONT, pid, NULL, NULL) == -1) {
    perror("Failed: PTRACE_CONT");
    exit(1);
  }
}

void ptrace_detatch(pid_t pid) {
  if (ptrace(PTRACE_DETACH, pid, NULL, NULL) == -1) {
    perror("Failed: PTRACE_DETACH");
    exit(1);
  }
}

struct memdata *inject_mem(pid_t pid, uint64_t addr, long val, bool make_md) {
  long old_val;

  old_val = ptrace(PTRACE_PEEKDATA, pid, addr, NULL);
#ifdef PTRACE_DEBUG
    printf("INJECT\n");
    printf("Addr: %lx\n", addr);
    printf("Old: %x\n", old_val);
    printf("New: %x\n", val);
#endif
  if (old_val == -1) {
    perror("Failed: PTRACE_PEEKDATA");
    exit(1);
  }

  if (ptrace(PTRACE_POKEDATA, pid, addr, val) == -1) {
    perror("Failed to PTRACE_POKEDATA");
    exit(1);
  }

  if (make_md) {
    struct memdata *new_md = malloc(sizeof(struct memdata));
    new_md->addr = addr;
    new_md->val = old_val;
    new_md->next = NULL;
    return new_md;
  }

  return NULL;
}

struct memdata *append_md(struct memdata *head, struct memdata *new_val) {
  if (head == NULL)
    return new_val;

  new_val->next = head;
  return new_val;
}

void restore_mem(pid_t pid, struct memdata *md) {
  struct memdata *md_ptr = md;
  struct memdata *tmp_md_ptr;
  while (md_ptr != NULL) {
#ifdef PTRACE_DEBUG
    printf("RESTORE\n");
    printf("Addr: %lx\n", md_ptr->addr);
    printf("Val: %x\n", md_ptr->val);
#endif
    inject_mem(pid, md_ptr->addr, md_ptr->val, false);
    tmp_md_ptr = md_ptr;
    md_ptr = md_ptr->next;
    free(tmp_md_ptr);
  }
}

void display_registers_for(pid_t pid) {
  struct user_regs_struct registers;
  // TODO This fails incorrectly?
	ptrace(PTRACE_GETREGS, pid, 0, &registers);
  display_registers(&registers);
}

int inject_open_shm(pid_t pid) {
  struct user_regs_struct regs, temp_regs;
  struct memdata *md = NULL;

  if (ptrace(PTRACE_GETREGS, pid, 0, &regs) == -1) {
    perror("FAILED: ptrace_getregs");
    exit(1);
  }

  long str_vals[] = {
    0x6d68732f7665642f, // /dev/shm
    0x6c6c6f636e77702f,
    0x656765, // ege
  };

  // TODO: Hardcoded limit
  for (int i = 0; i < 3; i++) {
    long val = str_vals[i];
    md = append_md(md, inject_mem(pid, regs.rsp + 8 * i, val, true));
  }

  memcpy(&temp_regs, &regs, sizeof(struct user_regs_struct));
  temp_regs.rax = 2;
  temp_regs.rdi = regs.rsp; 
  temp_regs.rsi = 2; // O_RDONLY // 2 = RDWR
  temp_regs.rdx = 7;
  inject_regs(pid, &temp_regs);
  md = append_md(md, inject_mem(pid, temp_regs.rip, 0xCC050F, true));
  md = append_md(md, inject_mem(pid, temp_regs.rip + 4, 0xCC, true));

  ptrace_cont(pid);
  waitpid(pid, NULL, 0);

  // Obtain RAX for file descriptor
  if (ptrace(PTRACE_GETREGS, pid, 0, &temp_regs) == -1) {
    perror("FAILED: ptrace_getregs");
    exit(1);
  }

  // Put everything back
  inject_regs(pid, &regs);
  restore_mem(pid, md);

  return (int) temp_regs.rax;
}

void inject_mmap(pid_t pid, int fd) {
  struct user_regs_struct temp_regs, regs;
  struct memdata *md = NULL;
  long int rip_instr;

  if (ptrace(PTRACE_GETREGS, pid, 0, &regs) == -1) {
    perror("FAILED: ptrace_getregs");
    exit(1);
  }

  memcpy(&temp_regs, &regs, sizeof(struct user_regs_struct));
  
  // We will construct an mmap syscall in the registers
  //mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset)

  temp_regs.rax = 9;
  temp_regs.rdi = mmap_addr;
  temp_regs.rsi = SHM_SIZE;
  temp_regs.rdx = PROT_READ | PROT_WRITE;
  temp_regs.r10 = MAP_SHARED | MAP_POPULATE;
  temp_regs.r8 = fd;
  temp_regs.r9 = 0;
  inject_regs(pid, &temp_regs);

  // Overwrite mem at RIP and perform a syscall
  md = append_md(md, inject_mem(pid, temp_regs.rip, 0xCC050F, true));
  md = append_md(md, inject_mem(pid, temp_regs.rip + 4, 0xCC, true));

  ptrace_cont(pid);
  waitpid(pid, NULL, 0);

  // Then restore registers, mem, and continue
  inject_regs(pid, &regs);
  restore_mem(pid, md);
}

void inject_drop_privs(pid_t pid) {
  struct user_regs_struct regs, temp_regs;
  struct memdata *md = NULL;
  long int rip_instr;

  if (ptrace(PTRACE_GETREGS, pid, 0, &regs) == -1) {
    perror("FAILED: ptrace_getregs");
    exit(1);
  }
  memcpy(&temp_regs, &regs, sizeof(struct user_regs_struct));

  // We will construct a seteuid syscall in the registers
  // mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset)

  // getuid
  temp_regs.rax = 102;
  inject_regs(pid, &temp_regs);

  // Overwrite mem at RIP and perform a syscall
  md = append_md(md, inject_mem(pid, temp_regs.rip, 0xCC050F, true));

  ptrace_cont(pid);
  waitpid(pid, NULL, 0);

  // TODO: pull from register
  if (ptrace(PTRACE_GETREGS, pid, 0, &temp_regs) == -1) {
    perror("FAILED: ptrace_getregs");
    exit(1);
  }

  int old_uid = temp_regs.rax;

  // setreuid
  memcpy(&temp_regs, &regs, sizeof(struct user_regs_struct));
  temp_regs.rax = 113;
  temp_regs.rdi = old_uid;
  temp_regs.rsi = old_uid;
  inject_regs(pid, &temp_regs);

  md = append_md(md, inject_mem(pid, temp_regs.rip, 0xCC050F, true));
  md = append_md(md, inject_mem(pid, temp_regs.rip + 4, 0xCC, true));

  ptrace_cont(pid);
  waitpid(pid, NULL, 0);

  // Then restore registers, mem, and continue
  inject_regs(pid, &regs);
  restore_mem(pid, md);
}

