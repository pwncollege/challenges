
#include <capstone/capstone.h>

#define CAPSTONE_ARCH CS_ARCH_X86
#define CAPSTONE_MODE CS_MODE_64

void print_disassembly(void *shellcode_addr, size_t shellcode_size)
{
  csh handle;
  cs_insn *insn;
  size_t count;

  if (cs_open(CAPSTONE_ARCH, CAPSTONE_MODE, &handle) != CS_ERR_OK) {
    printf("ERROR: disassembler failed to initialize.\n");
    return;
  }

  count = cs_disasm(handle, shellcode_addr, shellcode_size, (uint64_t)shellcode_addr, 0, &insn);
  if (count > 0) {
    size_t j;
    printf("      Address      |                      Bytes                    |          Instructions\n");
    printf("------------------------------------------------------------------------------------------\n");

    for (j = 0; j < count; j++) {
      printf("0x%016lx | ", (unsigned long)insn[j].address);
      for (int k = 0; k < insn[j].size; k++) printf("%02hhx ", insn[j].bytes[k]);
      for (int k = insn[j].size; k < 15; k++) printf("   ");
      printf(" | %s %s\n", insn[j].mnemonic, insn[j].op_str);
    }

    cs_free(insn, count);
  }
  else {
    printf("ERROR: Failed to disassemble shellcode! Bytes are:\n\n");
    printf("      Address      |                      Bytes\n");
    printf("--------------------------------------------------------------------\n");
    for (unsigned int i = 0; i <= shellcode_size; i += 16)
      {
        printf("0x%016lx | ", (unsigned long)shellcode_addr+i);
        for (int k = 0; k < 16; k++) printf("%02hhx ", ((uint8_t*)shellcode_addr)[i+k]);
        printf("\n");
      }
  }

  cs_close(&handle);
}
