uint64_t sp_;
uint64_t bp_;
uint64_t sz_;
uint64_t cp_;
uint64_t cv_;
uint64_t si_;
uint64_t rp_;

#define GET_SP(sp) asm volatile ("mov %0, SP" : "=r"(sp) : : );
#define GET_BP(bp) asm volatile ("mov %0, FP" : "=r"(bp) : : );
#define GET_FRAME_WORDS(sz_, sp, bp, rp_) GET_SP(sp); GET_BP(bp); sz_ = (bp-sp)/8+2; rp_ = bp+0x8;

void DUMP_STACK(uint64_t sp, uint64_t n)
{
  printf("+---------------------------------+-------------------------+--------------------+\n");
  printf("| %31s | %23s | %18s |\n", "Stack location", "Data (bytes)", "Data (LE int)");
  printf("+---------------------------------+-------------------------+--------------------+\n");
  for (si_ = 0; si_ < n; si_++) {
    printf("| 0x%016lx (rsp+0x%04x) | %02x %02x %02x %02x %02x %02x %02x %02x | 0x%016lx |\n",
           sp+8*si_, 8*si_,
           *(uint8_t *)(sp+8*si_+0), *(uint8_t *)(sp+8*si_+1), *(uint8_t *)(sp+8*si_+2), *(uint8_t *)(sp+8*si_+3),
           *(uint8_t *)(sp+8*si_+4), *(uint8_t *)(sp+8*si_+5), *(uint8_t *)(sp+8*si_+6), *(uint8_t *)(sp+8*si_+7),
           *(uint64_t *)(sp+8*si_)
           );
  }
  printf("+---------------------------------+-------------------------+--------------------+\n");
}
