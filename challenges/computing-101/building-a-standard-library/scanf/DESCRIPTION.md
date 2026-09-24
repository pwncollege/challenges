Your `sscanf` can parse text once it is in memory.
Your earlier `read` programs can put input there.
Combine them into `scanf(format, destinations)`.

This function uses a 256-byte scratch buffer, makes one `read` from standard input for at most 255 bytes, and adds a NUL immediately after the bytes that `read` returned.
It then calls your `sscanf` on that buffer and returns the scanner's assignment count.

For this level, assume that one successful `read` supplies the complete, valid input for the call.
It contains between 1 and 255 bytes.

The format and destination-array pointers arrive in `rdi` and `rsi`.
Keep the scanner's existing conversion and storage contracts.
Your buffer belongs to this call; it need not keep its contents after the function returns.

Export `.global scanf`, `.global sscanf`, and `.global parse_integer`, preserve the calling convention, and submit your shared library to `/challenge/check`.
