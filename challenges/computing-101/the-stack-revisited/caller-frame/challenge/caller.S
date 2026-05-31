/*
 * Hand-written caller that owns a known stack layout when it invokes solve.
 *
 * Call site:   void caller(void (*solve)(void), const char *flag_buf);
 *
 * caller copies 64 bytes from flag_buf into its own local region, at an
 * offset such that solve sees those bytes at [rsp + 0x40] from solve's own
 * perspective (after `call rdi` pushed the return address).
 *
 * On entry to solve, the layout from solve's `rsp` upward is:
 *
 *   [rsp + 0x00]  return address back into this function
 *   [rsp + 0x08]  start of caller's 0x80-byte local region
 *   ...
 *   [rsp + 0x40]  the 64-byte flag (copied from flag_buf)
 *   ...
 *   [rsp + 0x80]  caller's stashed solve fn pointer (internal bookkeeping)
 *   [rsp + 0x88]  saved rbp
 *   [rsp + 0x90]  return address back into main
 *
 * `push rbp` and `sub rsp, 0x80` leave rsp 16-byte-misaligned by 8 at the
 * `call rdi` site, so that the call's own push lands solve at a properly
 * 16-byte-aligned rsp -- matching the SysV AMD64 ABI -- otherwise a
 * student who tries to add SSE-using code inside solve would crash for a
 * reason unrelated to the lesson.
 */
.intel_syntax noprefix
.text
.global caller
.type caller, @function
caller:
    push rbp
    mov  rbp, rsp
    sub  rsp, 0x80

    mov  [rsp + 0x78], rdi      // stash solve fn pointer

    // copy 64 bytes from rsi (flag_buf) into [rsp + 0x38].
    // solve will see this region at [rsp + 0x40] after `call rdi`.
    mov  rcx, 8                 // 8 qwords = 64 bytes
    lea  rdi, [rsp + 0x38]      // destination
    rep  movsq                  // memcpy from [rsi] to [rdi]

    mov  rdi, [rsp + 0x78]      // restore solve fn pointer into rdi
    call rdi

    mov  rsp, rbp
    pop  rbp
    ret
.size caller, .-caller
