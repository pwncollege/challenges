One digit was easy.
A two-digit number like `42` needs *splitting* into its tens (`4`) and ones (`2`) --- and splitting is division: `42 / 10 = 4` (the quotient), and `42 % 10 = 2` (the remainder).

x86 gives you *both* results from one `div`, but `div` is a fussy instruction worth learning carefully.
`div rcx` divides the **128-bit** value resulting by concatenating `rdx:rax` by `rcx`, leaving the quotient in `rax` and the remainder in `rdx`.
Two things follow from that:

- It divides `rdx:rax`, not just `rax`, so you must clear `rdx` first (`xor rdx, rdx`) --- otherwise `div` treats leftover garbage as the high half of your number (and may crash).
- The divisor comes from a register, not an immediate, so load the `10` into one (e.g., `mov rcx, 10; div rcx`).
- You don't control the dividend: it's _always_ `rdx:rax`.

After the `div`, `rax` holds the tens and `rdx` holds the ones.
Turn each into a character the way `itoa_digit` did (add `0x30`) and store the two of them.

Write `itoa(value, buf)`, which we'll call from the challenge.
This function should take a value (`10`-`99`) in `rdi` and a pointer to the "output" buffer in `rsi`.
You should parse the number in `rdi` into two characters and write these two characters to that buffer.
Then return the number of characters written (in this case, 2).
Remember to `.global itoa`.

This is tricky, but do it carefully, and the flag is your reward!
