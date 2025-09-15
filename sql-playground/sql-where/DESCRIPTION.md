Any non-trivial database will have enough data in it that one must be _selective_ (🥁) about what you access.
Luckily, the `SELECT` query can be filtered with the `WHERE` clause!
This challenge will require you to filter your data, because now there's lots of junk in the database!

The challenge links to the SQLite documentation for the WHERE clause, and we'd like you to go and read it.
The TLDR, to get you started, is that you can append `WHERE condition` to your query, where `condition` is some expression you specify, like `some_column < 10` (for integer comparisons) or `some_column = 'pwn'` (for string comparisons) or the like.

You'll need to analyze the code to understand what differentiates the flag from the junk data, and then query on it!
Hint: it's the new column we added.
Can you make the right filter and filter your data to just the flag?