A number may have some space before it.
Extend your `sscanf` so `%d` skips leading whitespace before calling the integer parser.

Whitespace in the format has a related job: it consumes any amount of whitespace in the input, including none.
A space in the format can therefore match a tab in the input, several spaces, or no characters at all.
The ASCII whitespace bytes are space (`0x20`), tab (`0x09`), newline (`0x0a`), vertical tab (`0x0b`), form feed (`0x0c`), and carriage return (`0x0d`).

```text
input:   "  -42"
format:  "%d"
result:  -42

input:   "42"
format:  " %d "
result:  42
```

Formats in this level contain exactly one `%d`, with optional whitespace around it.
The number and return-value contracts stay the same.
Export `.global sscanf` and `.global parse_integer`, build your shared library, and submit it to `/challenge/check`.
