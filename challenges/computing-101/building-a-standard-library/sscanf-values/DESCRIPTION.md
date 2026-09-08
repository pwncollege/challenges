Now let the format contain several `%d` conversions.
Each conversion uses the next pointer in the destination array, just as each marker in your formatter used the next argument.

Keep separate positions in the input string, the format string, and the destination array.
Resume scanning the input at the pointer returned by your integer parser.

```text
input:         "12 -34"
format:        "%d %d"
destinations:  [pointer to first integer, pointer to second integer]
stored values: 12, -34
return:        2
```

Handle one through eight conversions, with or without whitespace between them.
Every conversion has valid input; for example, `"%d%d"` can read `"12-34"` because the minus sign ends the first number and starts the second.
Return the number of assigned values, and keep each integer in its own eight-byte destination.

Export `.global sscanf` and `.global parse_integer`, build your shared library, and submit it to `/challenge/check`.
