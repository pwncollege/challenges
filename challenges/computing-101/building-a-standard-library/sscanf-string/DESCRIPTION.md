Add `%s` to read a word.
Like `%d`, it skips leading whitespace.
Then it copies bytes up to the next whitespace character or NUL and appends a NUL byte to the destination.

The next destination pointer now identifies either an eight-byte integer or a string buffer, depending on the format.
A format such as `"%d %s %d"` can read `"-17 + 29"` into two integers and an operator string.

Handle mixed formats with one through eight conversions.
The entire input is at most 255 bytes, and every string destination has room for 256 bytes, including its terminator.
Every conversion has valid input.
Return the number of assigned values and leave the input and format unchanged.

Export `.global sscanf` and `.global parse_integer`, build your shared library, and submit it to `/challenge/check`.
