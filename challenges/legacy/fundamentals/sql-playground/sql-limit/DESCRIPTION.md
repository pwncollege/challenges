You've been able to rely on your `WHERE` clause to filter things down to exactly one result, but in this challenge, we've taken away the flag tags that you relied on to filter out decoy flags!
Luckily, simple SQL queries tend to return data in the order that it was inserted into the database, and the real flag was inserted before the decoy flags (but after some of the garbage data).
All you need is to `LIMIT` your query to just `1` result, and that result should be your flag!
The challenge links you to the `LIMIT` documentation if you need it!
