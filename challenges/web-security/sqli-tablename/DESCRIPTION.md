So far, the database structure has been known to you (e.g., the name of the `users` table), allowing you to knowingly craft your queries.
As a developer, you might be tempted to prevent this by, say, randomizing your table names, so that an attacker can't specify them to query data that they are not supposed to.
Unfortunately, this is not the slam dunk that you might think it is.

Databases are complex and much too clever for their own good.
For example, almost all modern databases keep the database layout specification itself _in a table_.
Attackers can query this table to get the table names, field names, and whatever other information they might need!

In this level, the developers have randomized the name of the (previously known as) `users` table.
Find it, and find the flag!
