
#include <errno.h>
#include <capstone/capstone.h>

#define CAPSTONE_ARCH CS_ARCH_X86
#define CAPSTONE_MODE CS_MODE_64

void print_gadget(unsigned long *gadget_addr)
{
  csh handle;
  cs_insn *insn;
  size_t count;
  unsigned char vec[64];

  if (cs_open(CAPSTONE_ARCH, CAPSTONE_MODE, &handle) != CS_ERR_OK) {
    printf("ERROR: disassembler failed to initialize.\n");
    return;
  }

  printf("| 0x%016lx: ", (unsigned long)gadget_addr);

  int r = mincore((void *) ((uintptr_t)gadget_addr & ~0xfff), 64, vec);
  if (r < 0 && errno == ENOMEM) {
    printf("(UNMAPPED MEMORY)");
  }
  else {
    count = cs_disasm(handle, (void *)gadget_addr, 64, (uint64_t)gadget_addr, 0, &insn);
    if (count > 0) {
      for (size_t j = 0; j < count; j++) {
        printf("%s %s ; ", insn[j].mnemonic, insn[j].op_str);
        if (strcmp(insn[j].mnemonic, "ret") == 0 || strcmp(insn[j].mnemonic, "call") == 0) break;
      }

      cs_free(insn, count);
    }
    else {
      printf("(DISASSEMBLY ERROR) ");
      for (int k = 0; k < 16; k++) printf("%02hhx ", ((uint8_t*)gadget_addr)[k]);
    }
  }
  printf("\n");

  cs_close(&handle);
}

void print_chain(unsigned long **chain_addr, int chain_length)
{
  printf("\n+--- Printing %ld gadgets of ROP chain at %p.\n", chain_length, chain_addr);
  for (int i = 0; i < chain_length; i++) {
    print_gadget(*(chain_addr + i));
  }
  printf("\n");
}
