Let's move on to more advanced filtering.
We got rid of the flag tag in this challenge, and you'll need to filter on the actual values of the flag data!
Luckily, `SQLite` (and all SQL engines in general) provide some functions for working with strings, and you'll use the `substr` function here.
`substr(some_column, start, length)` extracts `length` characters starting from `start` (the first character is at position `1`, not `0` as it would be in a sane language) of column `some_column`.
You can use the result of this anywhere the query accepts expressions, such as in the `WHERE` clause to compare the resulting value against a string as in the previous challenge!