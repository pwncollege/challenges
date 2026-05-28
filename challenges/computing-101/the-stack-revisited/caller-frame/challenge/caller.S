/*
 * Hand-written caller that owns a known stack layout when it invokes solve.
 *
 * Call site:   uint64_t caller(uint64_t (*solve)(void), uint64_t secret);
 *
 * On entry to solve, the layout (from solve's rsp upward) is:
 *
 *   [rsp + 0x00]  return address back into this function
 *   [rsp + 0x08]  first byte of the 0x40-byte local region
 *   [rsp + 0x40]  the secret
 *   [rsp + 0x48]  saved rbp
 *   [rsp + 0x50]  return address back into main
 *
 * `push rbp` first so that `call rdi` happens with a 16-byte-aligned rsp,
 * matching the SysV AMD64 ABI -- otherwise a student who tries to add
 * SSE-using code inside solve would crash for a reason unrelated to the
 * lesson.
 */
.intel_syntax noprefix
.text
.global caller
.type caller, @function
caller:
    push rbp
    mov  rbp, rsp
    sub  rsp, 0x40
    mov  [rsp + 0x38], rsi
    call rdi
    mov  rsp, rbp
    pop  rbp
    ret
.size caller, .-caller
